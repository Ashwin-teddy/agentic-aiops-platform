from __future__ import annotations

from typing import Any

from kubernetes import client, config as k8s_config

from app.core.config.settings import settings
from app.tools.base.tool_interface import BaseTool, ToolResult


class KubernetesTool(BaseTool):
    name = "kubernetes"
    description = "Manage Kubernetes clusters, deployments, pods, and services"
    category = "container_orchestration"
    required_permissions = ["admin:access"]
    risk_score = 0.85

    def __init__(self) -> None:
        super().__init__()
        self._core_v1: client.CoreV1Api | None = None
        self._apps_v1: client.AppsV1Api | None = None

    async def initialize(self) -> None:
        try:
            if settings.k8s_in_cluster:
                k8s_config.load_incluster_config()
            else:
                k8s_config.load_kube_config(config_file=settings.kubeconfig_path)
            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.Apps_v1Api()
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Kubernetes client: {e}") from e

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "list_pods")
        namespace = kwargs.get("namespace", "default")
        try:
            if action == "list_pods":
                pods = self._core_v1.list_namespaced_pod(namespace)
                pod_list = [{"name": p.metadata.name, "status": p.status.phase, "node": p.spec.node_name} for p in pods.items]
                return ToolResult(success=True, data={"pods": pod_list})
            elif action == "get_pod":
                pod = self._core_v1.read_namespaced_pod(kwargs["pod_name"], namespace)
                return ToolResult(success=True, data={"name": pod.metadata.name, "status": pod.status.phase})
            elif action == "list_deployments":
                deps = self._apps_v1.list_namespaced_deployment(namespace)
                dep_list = [{"name": d.metadata.name, "replicas": d.spec.replicas, "ready": d.status.ready_replicas} for d in deps.items]
                return ToolResult(success=True, data={"deployments": dep_list})
            elif action == "scale_deployment":
                name = kwargs["name"]
                replicas = kwargs["replicas"]
                self._apps_v1.patch_namespaced_deployment_scale(name, namespace, {"spec": {"replicas": replicas}})
                return ToolResult(success=True, data={"message": f"Deployment {name} scaled to {replicas}"})
            elif action == "restart_deployment":
                import datetime
                name = kwargs["name"]
                self._apps_v1.patch_namespaced_deployment(name, namespace, {
                    "spec": {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow().isoformat()}}}}
                })
                return ToolResult(success=True, data={"message": f"Deployment {name} restarted"})
            elif action == "list_events":
                events = self._core_v1.list_namespaced_event(namespace)
                event_list = [{"type": e.type, "reason": e.reason, "message": e.message} for e in events.items[:20]]
                return ToolResult(success=True, data={"events": event_list})
            elif action == "get_logs":
                pod_name = kwargs["pod_name"]
                container = kwargs.get("container")
                logs = self._core_v1.read_namespaced_pod_log(pod_name, namespace, container=container)
                return ToolResult(success=True, data={"logs": logs[-5000:]})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
        return ToolResult(success=False, error=f"Unknown action: {action}")

    async def validate_params(self, **kwargs: Any) -> bool:
        return "action" in kwargs

    async def health_check(self) -> bool:
        try:
            await self.initialize()
            self._core_v1.list_namespace()
            return True
        except Exception:
            return False
