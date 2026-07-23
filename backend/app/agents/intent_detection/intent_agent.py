from __future__ import annotations

import json

from app.core.config.settings import settings
from app.core.llm.router import get_model_router
from app.core.llm.types import LLMMessage, TaskType
from app.domain.enums.intent import IntentType
from app.observability.logging import get_logger

logger = get_logger(__name__)

INTENT_DETECTION_PROMPT = """You are an intent detection system for an IT Operations AI assistant.
Analyze the user message and classify it into one of these intents:

1. **troubleshooting** - User is reporting an issue, error, outage, performance problem, or needs help diagnosing something. Keywords: error, down, slow, failing, broken, issue, alert, incident, 500, timeout, crash, bug, not working.

2. **low_risk_access** - User wants read-only or low-privilege access to standard tools. Examples: Jira read access, Confluence read access, GitHub read access, View-only dashboard access, Read-only AWS console.

3. **high_risk_access** - User wants elevated, admin, or production access. Examples: Production database access, Admin role, Kubernetes cluster admin, AWS administrator, Write/modify production systems, Delete permissions.

4. **general_inquiry** - General questions about processes, documentation, how-to, or informational queries.

Respond with a JSON object:
{
    "intent": "<intent_type>",
    "confidence": <0.0-1.0>,
    "entities": {
        "resource_type": "<if access request>",
        "resource_identifier": "<specific resource>",
        "access_level": "<read/write/admin>",
        "affected_service": "<if troubleshooting>"
    },
    "reasoning": "<brief explanation>"
}

Only respond with the JSON object, nothing else."""


class IntentDetectionAgent:
    name = "intent_detection_agent"

    def __init__(self) -> None:
        self.router = get_model_router()

    async def detect(self, user_message: str, context: dict | None = None) -> dict:
        context_info = ""
        if context:
            context_info = f"\nAdditional context: {context}"
        messages = [
            LLMMessage(role="system", content=INTENT_DETECTION_PROMPT),
            LLMMessage(role="user", content=f"User message: {user_message}{context_info}"),
        ]
        try:
            response = await self.router.chat(
                messages=messages,
                task=TaskType.INTENT_DETECTION,
                model=settings.default_intent_model or None,
                temperature=0.0,
                max_tokens=500,
                json_mode=True,
            )
            result = json.loads(response.content)
            intent_str = result.get("intent", "general_inquiry")
            try:
                intent = IntentType(intent_str)
            except ValueError:
                intent = IntentType.UNKNOWN
            logger.info(
                "intent_detected",
                intent=intent.value,
                confidence=result.get("confidence", 0),
                model=response.model,
                provider=response.provider.value,
            )
            return {
                "intent": intent,
                "confidence": result.get("confidence", 0.5),
                "entities": result.get("entities", {}),
                "reasoning": result.get("reasoning", ""),
            }
        except Exception as e:
            logger.error("intent_detection_failed", error=str(e))
            return {
                "intent": IntentType.UNKNOWN,
                "confidence": 0.0,
                "entities": {},
                "reasoning": f"Detection failed: {e}",
            }
