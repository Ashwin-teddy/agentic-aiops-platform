__all__ = [
    "IntentDetectionAgent",
    "PlannerAgent",
    "TroubleshootingAgent",
    "RAGAgent",
    "PolicyAgent",
    "AccessManagementAgent",
    "HumanApprovalAgent",
    "NotificationAgent",
    "AuditAgent",
    "MemoryManager",
    "AIOpsWorkflow",
    "get_aiops_workflow",
]

_MAP = {
    "IntentDetectionAgent": "app.agents.intent_detection.intent_agent",
    "PlannerAgent": "app.agents.planner.planner_agent",
    "TroubleshootingAgent": "app.agents.troubleshooting.troubleshooting_agent",
    "RAGAgent": "app.agents.rag.rag_agent",
    "PolicyAgent": "app.agents.policy.policy_agent",
    "AccessManagementAgent": "app.agents.access_management.access_agent",
    "HumanApprovalAgent": "app.agents.human_approval.approval_agent",
    "NotificationAgent": "app.agents.notification.notification_agent",
    "AuditAgent": "app.agents.audit.audit_agent",
    "MemoryManager": "app.agents.memory.memory_agent",
    "AIOpsWorkflow": "app.agents.workflow.aiops_workflow",
    "get_aiops_workflow": "app.agents.workflow.aiops_workflow",
}


def _lazy_import(name: str):
    import importlib

    if name in _MAP:
        mod = importlib.import_module(_MAP[name])
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __getattr__(name: str):
    return _lazy_import(name)
