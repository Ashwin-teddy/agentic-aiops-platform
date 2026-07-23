from __future__ import annotations

import json

from app.core.config.settings import settings
from app.core.llm.router import get_model_router
from app.core.llm.types import LLMMessage, TaskType
from app.domain.enums.intent import IntentType
from app.observability.logging import get_logger

logger = get_logger(__name__)

PLANNER_PROMPT = """You are a planning agent for an IT Operations AI system.
Given the detected intent and context, create a step-by-step execution plan.

Intent: {intent}
Entities: {entities}
Available tools: {tools}
User context: {context}

Create a JSON plan with:
{{
    "workflow_type": "<troubleshooting|access_request|incident_response>",
    "risk_level": "<low|medium|high|critical>",
    "steps": [
        {{
            "step_id": 1,
            "agent": "<agent_name>",
            "action": "<action_description>",
            "tool": "<tool_name_if_needed>",
            "parameters": {{}},
            "depends_on": [],
            "requires_approval": false
        }}
    ],
    "estimated_duration_seconds": <number>,
    "required_approvals": ["<approval_types>"]
}}

Available agents: intent_detection, troubleshooting, rag, policy, access_management, human_approval, notification, audit, memory

For troubleshooting, include steps: collect logs, collect metrics, search knowledge, analyze root cause, recommend remediation.
For access requests, include steps: evaluate policy, check risk, execute or route to approval.
Always include: audit_log and notify_user as final steps.

Respond with only the JSON plan."""


class PlannerAgent:
    name = "planner_agent"

    def __init__(self) -> None:
        self.router = get_model_router()

    async def create_plan(
        self,
        intent: IntentType,
        entities: dict,
        available_tools: list[dict],
        context: dict | None = None,
    ) -> dict:
        messages = [
            LLMMessage(role="system", content=PLANNER_PROMPT.format(
                intent=intent.value,
                entities=json.dumps(entities),
                tools=json.dumps([t["name"] for t in available_tools]),
                context=json.dumps(context or {}),
            )),
            LLMMessage(role="user", content="Create an execution plan for this request."),
        ]
        try:
            response = await self.router.chat(
                messages=messages,
                task=TaskType.PLANNING,
                model=settings.default_planning_model or None,
                temperature=0.0,
                max_tokens=2000,
                json_mode=True,
            )
            plan = json.loads(response.content)
            logger.info(
                "plan_created",
                steps=len(plan.get("steps", [])),
                workflow=plan.get("workflow_type"),
                model=response.model,
            )
            return plan
        except Exception as e:
            logger.error("planning_failed", error=str(e))
            return self._fallback_plan(intent, entities)

    def _fallback_plan(self, intent: IntentType, entities: dict) -> dict:
        if intent == IntentType.TROUBLESHOOTING:
            return {
                "workflow_type": "troubleshooting",
                "risk_level": "low",
                "steps": [
                    {"step_id": 1, "agent": "troubleshooting", "action": "collect_diagnostics", "depends_on": []},
                    {"step_id": 2, "agent": "rag", "action": "search_knowledge", "depends_on": [1]},
                    {"step_id": 3, "agent": "troubleshooting", "action": "analyze_root_cause", "depends_on": [1, 2]},
                    {"step_id": 4, "agent": "notification", "action": "notify_user", "depends_on": [3]},
                    {"step_id": 5, "agent": "audit", "action": "log_execution", "depends_on": [3]},
                ],
                "estimated_duration_seconds": 120,
                "required_approvals": [],
            }
        elif intent in (IntentType.LOW_RISK_ACCESS, IntentType.HIGH_RISK_ACCESS):
            return {
                "workflow_type": "access_request",
                "risk_level": "low" if intent == IntentType.LOW_RISK_ACCESS else "high",
                "steps": [
                    {"step_id": 1, "agent": "policy", "action": "evaluate_risk", "depends_on": []},
                    {"step_id": 2, "agent": "access_management", "action": "process_request", "depends_on": [1]},
                    {"step_id": 3, "agent": "human_approval", "action": "get_approval", "depends_on": [1], "requires_approval": True},
                    {"step_id": 4, "agent": "notification", "action": "notify_user", "depends_on": [2, 3]},
                    {"step_id": 5, "agent": "audit", "action": "log_execution", "depends_on": [2]},
                ],
                "estimated_duration_seconds": 60,
                "required_approvals": ["manager", "security"] if intent == IntentType.HIGH_RISK_ACCESS else [],
            }
        return {
            "workflow_type": "general",
            "risk_level": "low",
            "steps": [
                {"step_id": 1, "agent": "rag", "action": "search_knowledge", "depends_on": []},
                {"step_id": 2, "agent": "notification", "action": "notify_user", "depends_on": [1]},
            ],
            "estimated_duration_seconds": 30,
            "required_approvals": [],
        }
