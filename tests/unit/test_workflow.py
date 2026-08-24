from __future__ import annotations

import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.workflow.aiops_workflow import AIOpsState, AIOpsWorkflow


@pytest.fixture
def workflow():
    with patch("app.agents.workflow.aiops_workflow.get_tool_registry"):
        with patch("app.agents.workflow.aiops_workflow.IntentDetectionAgent"):
            with patch("app.agents.workflow.aiops_workflow.PlannerAgent"):
                with patch("app.agents.workflow.aiops_workflow.TroubleshootingAgent"):
                    with patch("app.agents.workflow.aiops_workflow.RAGAgent"):
                        with patch("app.agents.workflow.aiops_workflow.PolicyAgent"):
                            with patch("app.agents.workflow.aiops_workflow.AccessManagementAgent"):
                                with patch("app.agents.workflow.aiops_workflow.HumanApprovalAgent"):
                                    with patch("app.agents.workflow.aiops_workflow.NotificationAgent"):
                                        with patch("app.agents.workflow.aiops_workflow.AuditAgent"):
                                            with patch("app.agents.workflow.aiops_workflow.MemoryManager"):
                                                with patch("app.agents.workflow.aiops_workflow.MemorySaver"):
                                                    w = AIOpsWorkflow.__new__(AIOpsWorkflow)
                                                    w.intent_agent = MagicMock()
                                                    w.planner_agent = MagicMock()
                                                    w.troubleshooting_agent = MagicMock()
                                                    w.rag_agent = MagicMock()
                                                    w.policy_agent = MagicMock()
                                                    w.access_agent = MagicMock()
                                                    w.approval_agent = MagicMock()
                                                    w.notification_agent = MagicMock()
                                                    w.audit_agent = MagicMock()
                                                    w.memory_manager = MagicMock()
                                                    w.tool_registry = MagicMock()
                                                    w.memory = MagicMock()
                                                    w.graph = MagicMock()
                                                    return w


def _make_state(**overrides) -> AIOpsState:
    base: dict[str, Any] = {
        "session_id": "test-session",
        "user_id": "user-1",
        "user_message": "test",
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
        "metadata": {},
        "start_time": time.monotonic(),
    }
    base.update(overrides)
    return base


class TestRouteByIntent:
    def test_troubleshooting_routes(self, workflow):
        state = _make_state(intent="troubleshooting")
        assert workflow._route_by_intent(state) == "troubleshooting"

    def test_low_risk_access_routes(self, workflow):
        state = _make_state(intent="low_risk_access")
        assert workflow._route_by_intent(state) == "low_risk_access"

    def test_high_risk_access_routes(self, workflow):
        state = _make_state(intent="high_risk_access")
        assert workflow._route_by_intent(state) == "high_risk_access"

    def test_general_routes_to_general(self, workflow):
        state = _make_state(intent="general")
        assert workflow._route_by_intent(state) == "general"

    def test_unknown_intent_routes_to_general(self, workflow):
        state = _make_state(intent="something_else")
        assert workflow._route_by_intent(state) == "general"


class TestRouteByRisk:
    def test_auto_approve(self, workflow):
        state = _make_state(risk_evaluation={"auto_approve": True})
        assert workflow._route_by_risk(state) == "auto_approve"

    def test_needs_approval(self, workflow):
        state = _make_state(risk_evaluation={"auto_approve": False})
        assert workflow._route_by_risk(state) == "needs_approval"

    def test_missing_risk_evaluation(self, workflow):
        state = _make_state(risk_evaluation={})
        assert workflow._route_by_risk(state) == "needs_approval"


class TestNodeErrorHandling:
    @pytest.mark.asyncio
    async def test_detect_intent_handles_exception(self, workflow):
        workflow.intent_agent.detect = AsyncMock(side_effect=RuntimeError("LLM down"))
        state = _make_state(user_message="test")
        result = await workflow._detect_intent_node(state)
        assert result["status"] == "intent_detection_failed"
        assert result["error"] == "LLM down"
        assert result["intent"] == "general"

    @pytest.mark.asyncio
    async def test_plan_handles_exception(self, workflow):
        workflow.planner_agent.create_plan = AsyncMock(side_effect=RuntimeError("planner error"))
        state = _make_state(intent="troubleshooting")
        result = await workflow._plan_node(state)
        assert result["status"] == "planning_failed"
        assert "planner error" in result["error"]

    @pytest.mark.asyncio
    async def test_search_knowledge_handles_exception(self, workflow):
        workflow.rag_agent.search_knowledge = AsyncMock(side_effect=RuntimeError("qdrant down"))
        state = _make_state(user_message="test")
        result = await workflow._search_knowledge_node(state)
        assert result["status"] == "knowledge_search_failed"
        assert "qdrant down" in result["error"]

    @pytest.mark.asyncio
    async def test_evaluate_risk_handles_exception(self, workflow):
        workflow.policy_agent.evaluate_risk = AsyncMock(side_effect=RuntimeError("policy error"))
        state = _make_state(entities={"resource_type": "vm"})
        result = await workflow._evaluate_risk_node(state)
        assert result["status"] == "risk_evaluation_failed"
        assert result["risk_evaluation"]["auto_approve"] is False

    @pytest.mark.asyncio
    async def test_run_handles_graph_exception(self, workflow):
        workflow.memory_manager.initialize_session = AsyncMock(return_value="session-1")
        workflow.graph.ainvoke = AsyncMock(side_effect=RuntimeError("graph crash"))
        result = await workflow.run(user_message="test", user_id="user-1")
        assert result["status"] == "failed"
        assert "error" in result["metadata"]
