from __future__ import annotations

import json
from typing import Any

from app.core.config.settings import settings
from app.core.llm.router import get_model_router
from app.core.llm.types import LLMMessage, TaskType
from app.observability.logging import get_logger
from app.rag.retrieval.retriever import RAGRetriever
from app.tools.base.tool_registry import get_tool_registry

logger = get_logger(__name__)

TROUBLESHOOT_PROMPT = """You are an expert IT troubleshooting agent.
Analyze the following diagnostic data and determine root cause and remediation.

Service: {service}
Affected components: {components}
Diagnostic data:
{diagnostics}

Knowledge base context:
{knowledge_context}

Provide a JSON response:
{{
    "root_cause_analysis": "<detailed root cause>",
    "severity": "<P1|P2|P3|P4>",
    "affected_services": ["<list>"],
    "recommended_remediation": [
        {{
            "action": "<description>",
            "tool": "<tool_name_if_automated>",
            "parameters": {{}},
            "risk_level": "<low|medium|high>",
            "automated": false
        }}
    ],
    "prevention_recommendations": ["<list>"],
    "similar_past_incidents": ["<list if any>"],
    "requires_rollback": false,
    "estimated_resolution_time": "<time estimate>"
}}"""


class TroubleshootingAgent:
    name = "troubleshooting_agent"

    def __init__(self) -> None:
        self.router = get_model_router()
        self.rag_retriever = RAGRetriever()
        self.tool_registry = get_tool_registry()

    async def diagnose(
        self,
        service: str,
        components: list[str],
        diagnostic_data: dict[str, Any],
        session_id: str = "",
    ) -> dict[str, Any]:
        knowledge_context = "No relevant knowledge found."
        try:
            query = f"troubleshooting {service} " + " ".join(components)
            results = await self.rag_retriever.retrieve(query)
            formatted = self.rag_retriever.format_with_citations(results)
            knowledge_context = formatted["answer_context"]
        except Exception as e:
            logger.error("rag_retrieval_failed", error=str(e))

        messages = [
            LLMMessage(role="system", content=TROUBLESHOOT_PROMPT.format(
                service=service,
                components=", ".join(components),
                diagnostics=str(diagnostic_data)[:8000],
                knowledge_context=knowledge_context[:4000],
            )),
            LLMMessage(role="user", content="Analyze the above diagnostic data and provide root cause analysis and remediation steps."),
        ]
        try:
            response = await self.router.chat(
                messages=messages,
                task=TaskType.TROUBLESHOOTING,
                model=settings.default_troubleshooting_model or None,
                temperature=0.1,
                max_tokens=4000,
                json_mode=True,
            )
            result = json.loads(response.content)
            logger.info(
                "diagnosis_complete",
                service=service,
                root_cause_length=len(result.get("root_cause_analysis", "")),
                model=response.model,
            )
            return result
        except Exception as e:
            logger.error("diagnosis_failed", error=str(e))
            return {"root_cause_analysis": f"Analysis failed: {e}", "recommended_remediation": []}

    async def collect_diagnostics(self, service: str, namespace: str = "default") -> dict[str, Any]:
        diagnostics: dict[str, Any] = {}
        k8s_tool = self.tool_registry.get("kubernetes")
        if k8s_tool:
            try:
                pod_result = await k8s_tool.safe_execute(action="list_pods", namespace=namespace)
                diagnostics["pods"] = pod_result.data if pod_result.success else {"error": pod_result.error}
            except Exception:
                pass
            try:
                events_result = await k8s_tool.safe_execute(action="list_events", namespace=namespace)
                diagnostics["events"] = events_result.data if events_result.success else {"error": events_result.error}
            except Exception:
                pass
            try:
                dep_result = await k8s_tool.safe_execute(action="list_deployments", namespace=namespace)
                diagnostics["deployments"] = dep_result.data if dep_result.success else {"error": dep_result.error}
            except Exception:
                pass
        sn_tool = self.tool_registry.get("servicenow")
        if sn_tool:
            try:
                kb_result = await sn_tool.safe_execute(action="search_knowledge", query=service)
                diagnostics["servicenow_kb"] = kb_result.data if kb_result.success else {"error": kb_result.error}
            except Exception:
                pass
        return diagnostics

    async def execute_remediation(self, remediation: dict[str, Any], dry_run: bool = True) -> dict[str, Any]:
        tool_name = remediation.get("tool")
        if not tool_name:
            return {"success": False, "error": "No tool specified for remediation"}
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        params = remediation.get("parameters", {})
        if dry_run:
            return {"success": True, "dry_run": True, "would_execute": {"tool": tool_name, "params": params}}
        return await tool.safe_execute(**params)
