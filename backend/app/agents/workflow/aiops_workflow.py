from __future__ import annotations

import time
import uuid
from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.access_management.access_agent import AccessManagementAgent
from app.agents.audit.audit_agent import AuditAgent
from app.agents.human_approval.approval_agent import HumanApprovalAgent
from app.agents.intent_detection.intent_agent import IntentDetectionAgent
from app.agents.memory.memory_agent import MemoryManager
from app.agents.notification.notification_agent import NotificationAgent
from app.agents.planner.planner_agent import PlannerAgent
from app.agents.policy.policy_agent import PolicyAgent
from app.agents.rag.rag_agent import RAGAgent
from app.agents.troubleshooting.troubleshooting_agent import TroubleshootingAgent
from app.domain.enums.intent import IntentType
from app.domain.enums.risk import RiskLevel
from app.observability.logging import get_logger
from app.tools.base.tool_registry import get_tool_registry

logger = get_logger(__name__)


class AIOpsState(TypedDict):
    session_id: str
    user_id: str
    user_message: str
    intent: str
    intent_confidence: float
    entities: dict[str, Any]
    plan: dict[str, Any]
    current_step: int
    diagnostics: dict[str, Any]
    knowledge_results: dict[str, Any]
    risk_evaluation: dict[str, Any]
    access_result: dict[str, Any]
    approval_result: dict[str, Any]
    diagnosis: dict[str, Any]
    remediation: dict[str, Any]
    notifications_sent: dict[str, Any]
    audit_entries: list[dict[str, Any]]
    response: str
    error: str | None
    status: str
    metadata: dict[str, Any]
    start_time: float


class AIOpsWorkflow:
    def __init__(self) -> None:
        self.intent_agent = IntentDetectionAgent()
        self.planner_agent = PlannerAgent()
        self.troubleshooting_agent = TroubleshootingAgent()
        self.rag_agent = RAGAgent()
        self.policy_agent = PolicyAgent()
        self.access_agent = AccessManagementAgent()
        self.approval_agent = HumanApprovalAgent()
        self.notification_agent = NotificationAgent()
        self.audit_agent = AuditAgent()
        self.memory_manager = MemoryManager()
        self.tool_registry = get_tool_registry()
        self.memory = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AIOpsState)
        workflow.add_node("detect_intent", self._detect_intent_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("troubleshoot_collect", self._troubleshoot_collect_node)
        workflow.add_node("search_knowledge", self._search_knowledge_node)
        workflow.add_node("analyze_root_cause", self._analyze_root_cause_node)
        workflow.add_node("evaluate_risk", self._evaluate_risk_node)
        workflow.add_node("process_access", self._process_access_node)
        workflow.add_node("request_approval", self._request_approval_node)
        workflow.add_node("execute_remediation", self._execute_remediation_node)
        workflow.add_node("notify", self._notify_node)
        workflow.add_node("audit", self._audit_node)
        workflow.add_node("finalize", self._finalize_node)

        workflow.set_entry_point("detect_intent")
        workflow.add_edge("detect_intent", "plan")
        workflow.add_conditional_edges(
            "plan",
            self._route_by_intent,
            {
                "troubleshooting": "troubleshoot_collect",
                "low_risk_access": "evaluate_risk",
                "high_risk_access": "evaluate_risk",
                "general": "search_knowledge",
            },
        )
        workflow.add_edge("troubleshoot_collect", "search_knowledge")
        workflow.add_edge("search_knowledge", "analyze_root_cause")
        workflow.add_edge("analyze_root_cause", "execute_remediation")
        workflow.add_conditional_edges(
            "evaluate_risk",
            self._route_by_risk,
            {
                "auto_approve": "process_access",
                "needs_approval": "request_approval",
            },
        )
        workflow.add_edge("process_access", "notify")
        workflow.add_edge("request_approval", "notify")
        workflow.add_edge("execute_remediation", "notify")
        workflow.add_edge("notify", "audit")
        workflow.add_edge("audit", "finalize")
        workflow.add_edge("finalize", END)
        return workflow.compile(checkpointer=self.memory)

    def _route_by_intent(self, state: AIOpsState) -> str:
        intent = state.get("intent", "general")
        if intent == IntentType.TROUBLESHOOTING.value:
            return "troubleshooting"
        if intent == IntentType.LOW_RISK_ACCESS.value:
            return "low_risk_access"
        if intent == IntentType.HIGH_RISK_ACCESS.value:
            return "high_risk_access"
        return "general"

    def _route_by_risk(self, state: AIOpsState) -> str:
        risk_eval = state.get("risk_evaluation", {})
        if risk_eval.get("auto_approve", False):
            return "auto_approve"
        return "needs_approval"

    async def _detect_intent_node(self, state: AIOpsState) -> dict[str, Any]:
        try:
            result = await self.intent_agent.detect(state["user_message"])
            return {
                "intent": result["intent"].value,
                "intent_confidence": result["confidence"],
                "entities": result["entities"],
                "status": "intent_detected",
            }
        except Exception as e:
            logger.error("detect_intent_failed", error=str(e))
            return {"intent": "general", "intent_confidence": 0.0, "entities": {}, "error": str(e), "status": "intent_detection_failed"}

    async def _plan_node(self, state: AIOpsState) -> dict[str, Any]:
        try:
            intent = IntentType(state["intent"])
            plan = await self.planner_agent.create_plan(
                intent=intent,
                entities=state["entities"],
                available_tools=self.tool_registry.list_tools(),
                context=state.get("metadata", {}),
            )
            return {"plan": plan, "current_step": 0, "status": "planned"}
        except Exception as e:
            logger.error("plan_failed", error=str(e))
            return {"plan": {}, "current_step": 0, "error": str(e), "status": "planning_failed"}

    async def _troubleshoot_collect_node(self, state: AIOpsState) -> dict[str, Any]:
        try:
            entities = state["entities"]
            service = entities.get("affected_service", "unknown")
            diagnostics = await self.troubleshooting_agent.collect_diagnostics(service=service)
            return {"diagnostics": diagnostics, "status": "diagnostics_collected"}
        except Exception as e:
            logger.error("troubleshoot_collect_failed", error=str(e))
            return {"diagnostics": {}, "error": str(e), "status": "diagnostics_failed"}

    async def _search_knowledge_node(self, state: AIOpsState) -> dict[str, Any]:
        try:
            query = state["user_message"]
            results = await self.rag_agent.search_knowledge(query)
            return {"knowledge_results": results, "status": "knowledge_searched"}
        except Exception as e:
            logger.error("search_knowledge_failed", error=str(e))
            return {"knowledge_results": {}, "error": str(e), "status": "knowledge_search_failed"}

    async def _analyze_root_cause_node(self, state: AIOpsState) -> dict[str, Any]:
        try:
            entities = state["entities"]
            service = entities.get("affected_service", "unknown")
            diagnosis = await self.troubleshooting_agent.diagnose(
                service=service,
                components=entities.get("components", []),
                diagnostic_data=state["diagnostics"],
                session_id=state["session_id"],
            )
            return {"diagnosis": diagnosis, "status": "root_cause_analyzed"}
        except Exception as e:
            logger.error("analyze_root_cause_failed", error=str(e))
            return {"diagnosis": {}, "error": str(e), "status": "root_cause_analysis_failed"}

    async def _evaluate_risk_node(self, state: AIOpsState) -> dict[str, Any]:
        try:
            entities = state["entities"]
            risk_eval = await self.policy_agent.evaluate_risk(
                resource_type=entities.get("resource_type", "unknown"),
                access_type=entities.get("access_level", "read"),
            )
            return {"risk_evaluation": risk_eval, "status": "risk_evaluated"}
        except Exception as e:
            logger.error("evaluate_risk_failed", error=str(e))
            return {"risk_evaluation": {"risk_level": "high", "risk_score": 1.0, "auto_approve": False}, "error": str(e), "status": "risk_evaluation_failed"}

    async def _process_access_node(self, state: AIOpsState) -> dict[str, Any]:
        try:
            entities = state["entities"]
            risk_level = RiskLevel(state["risk_evaluation"].get("risk_level", "low"))
            result = await self.access_agent.process_access_request(
                user_id=state["user_id"],
                resource_type=entities.get("resource_type", "unknown"),
                resource_identifier=entities.get("resource_identifier", ""),
                access_type=entities.get("access_level", "read"),
                risk_level=risk_level,
                justification=entities.get("justification", ""),
                auto_execute=True,
            )
            return {"access_result": result, "status": "access_processed"}
        except Exception as e:
            logger.error("process_access_failed", error=str(e))
            return {"access_result": {"status": "failed"}, "error": str(e), "status": "access_processing_failed"}

    async def _request_approval_node(self, state: AIOpsState) -> dict[str, Any]:
        try:
            entities = state["entities"]
            risk_level = RiskLevel(state["risk_evaluation"].get("risk_level", "medium"))
            risk_score = state["risk_evaluation"].get("risk_score", 0.5)
            requester_email = await self._get_user_email(state["user_id"])
            approval = await self.approval_agent.create_approval_request(
                request_id=str(uuid.uuid4()),
                requester_id=state["user_id"],
                requester_email=requester_email,
                resource_type=entities.get("resource_type", "unknown"),
                resource_identifier=entities.get("resource_identifier", ""),
                access_type=entities.get("access_level", "read"),
                risk_level=risk_level,
                risk_score=risk_score,
                justification=entities.get("justification", ""),
            )
            return {"approval_result": approval, "status": "approval_requested"}
        except Exception as e:
            logger.error("request_approval_failed", error=str(e))
            return {"approval_result": {"status": "failed"}, "error": str(e), "status": "approval_request_failed"}

    async def _get_user_email(self, user_id: str) -> str:
        try:
            from sqlalchemy import select

            from app.db.models.user import UserModel
            from app.db.session import get_session

            async with get_session() as session:
                result = await session.execute(
                    select(UserModel.email).where(UserModel.id == user_id)
                )
                row = result.scalar_one_or_none()
                return str(row) if row else ""
        except Exception:
            return ""

    async def _execute_remediation_node(self, state: AIOpsState) -> dict[str, Any]:
        try:
            diagnosis = state.get("diagnosis", {})
            remediation_steps = diagnosis.get("recommended_remediation", [])
            results: list[dict[str, Any]] = []
            for step in remediation_steps:
                if step.get("tool") and not step.get("automated", False):
                    result = await self.troubleshooting_agent.execute_remediation(step, dry_run=True)
                    results.append(result)
            return {
                "remediation": {"steps": remediation_steps, "results": results},
                "status": "remediation_executed",
            }
        except Exception as e:
            logger.error("execute_remediation_failed", error=str(e))
            return {"remediation": {"steps": [], "results": []}, "error": str(e), "status": "remediation_failed"}

    async def _notify_node(self, state: AIOpsState) -> dict[str, Any]:
        intent = state["intent"]
        if intent == IntentType.TROUBLESHOOTING.value:
            diagnosis = state.get("diagnosis", {})
            await self.notification_agent.notify_user(
                user_id=state["user_id"],
                message=f"Troubleshooting complete. Root cause: {diagnosis.get('root_cause_analysis', 'Analyzing...')[:500]}",
                title="Troubleshooting Update",
            )
        elif intent in (IntentType.LOW_RISK_ACCESS.value, IntentType.HIGH_RISK_ACCESS.value):
            risk_eval = state.get("risk_evaluation", {})
            if risk_eval.get("auto_approve"):
                await self.notification_agent.notify_user(
                    user_id=state["user_id"],
                    message="Your access request has been auto-approved.",
                    title="Access Request Approved",
                )
            else:
                await self.notification_agent.notify_user(
                    user_id=state["user_id"],
                    message="Your access request is pending approval.",
                    title="Access Request Pending",
                )
        return {"notifications_sent": {"status": "sent"}, "status": "notified"}

    async def _audit_node(self, state: AIOpsState) -> dict[str, Any]:
        entry = await self.audit_agent.log_action(
            user_id=state["user_id"],
            session_id=state["session_id"],
            action=f"workflow.{state['intent']}",
            details={
                "intent": state["intent"],
                "confidence": state["intent_confidence"],
                "entities": state["entities"],
                "status": state["status"],
            },
        )
        entries = state.get("audit_entries", [])
        entries.append(entry)
        return {"audit_entries": entries, "status": "audited"}

    async def _finalize_node(self, state: AIOpsState) -> dict[str, Any]:
        response = self._build_response(state)
        await self.memory_manager.add_conversation_turn(
            user_id=state["user_id"],
            session_id=state["session_id"],
            user_msg=state["user_message"],
            assistant_msg=response,
            intent=state["intent"],
        )
        elapsed = time.monotonic() - state["start_time"]
        return {
            "response": response,
            "status": "completed",
            "metadata": {**state.get("metadata", {}), "total_duration_s": round(elapsed, 2)},
        }

    def _build_response(self, state: AIOpsState) -> str:
        intent = state["intent"]
        if intent == IntentType.TROUBLESHOOTING.value:
            diagnosis = state.get("diagnosis", {})
            return (
                f"**Root Cause Analysis:**\n{diagnosis.get('root_cause_analysis', 'Pending analysis')}\n\n"
                f"**Recommended Remediation:**\n"
                + "\n".join(
                    f"- {r.get('action', 'N/A')}"
                    for r in diagnosis.get("recommended_remediation", [])
                )
            )
        if intent in (IntentType.LOW_RISK_ACCESS.value, IntentType.HIGH_RISK_ACCESS.value):
            risk_eval = state.get("risk_evaluation", {})
            access_result = state.get("access_result", {})
            approval_result = state.get("approval_result", {})
            if risk_eval.get("auto_approve"):
                return f"Your access request has been auto-approved. Status: {access_result.get('status', 'unknown')}"
            return (
                f"Your access request requires approval.\n"
                f"Risk Level: {risk_eval.get('risk_level', 'unknown')} (Score: {risk_eval.get('risk_score', 0):.2f})\n"
                f"Status: {approval_result.get('status', 'pending')}"
            )
        knowledge = state.get("knowledge_results", {})
        return knowledge.get(
            "answer", "I've searched our knowledge base. Please check the results."
        )

    async def run(
        self,
        user_message: str,
        user_id: str,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not session_id:
            session_id = await self.memory_manager.initialize_session(user_id)
        initial_state: AIOpsState = {
            "session_id": session_id,
            "user_id": user_id,
            "user_message": user_message,
            "intent": "",
            "intent_confidence": 0.0,
            "entities": {},
            "plan": {},
            "current_step": 0,
            "diagnostics": {},
            "knowledge_results": {},
            "risk_evaluation": {},
            "access_result": {},
            "approval_result": {},
            "diagnosis": {},
            "remediation": {},
            "notifications_sent": {},
            "audit_entries": [],
            "response": "",
            "error": None,
            "status": "initiated",
            "metadata": metadata or {},
            "start_time": time.monotonic(),
        }
        config = {"configurable": {"thread_id": session_id}}
        try:
            final_state = await self.graph.ainvoke(initial_state, config=config)
        except Exception as e:
            logger.error("workflow_execution_failed", error=str(e))
            return {
                "session_id": session_id,
                "response": "An error occurred while processing your request. Please try again.",
                "intent": "",
                "status": "failed",
                "metadata": {"error": str(e)},
            }
        return {
            "session_id": session_id,
            "response": final_state.get("response", ""),
            "intent": final_state.get("intent", ""),
            "status": final_state.get("status", ""),
            "metadata": final_state.get("metadata", {}),
        }


_workflow: AIOpsWorkflow | None = None


def get_aiops_workflow() -> AIOpsWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = AIOpsWorkflow()
    return _workflow
