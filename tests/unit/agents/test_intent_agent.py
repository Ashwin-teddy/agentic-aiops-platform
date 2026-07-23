from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from app.agents.intent_detection.intent_agent import IntentDetectionAgent
from app.domain.enums.intent import IntentType


class TestIntentDetectionAgent:
    @pytest.fixture
    def agent(self) -> IntentDetectionAgent:
        return IntentDetectionAgent()

    @pytest.mark.asyncio
    async def test_detect_troubleshooting_intent(self, agent: IntentDetectionAgent) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"intent": "troubleshooting", "confidence": 0.95, "entities": {"affected_service": "api-gateway"}, "reasoning": "User reports errors"}'))]
        with patch.object(agent.llm.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            result = await agent.detect("My API gateway is returning 500 errors")
            assert result["intent"] == IntentType.TROUBLESHOOTING
            assert result["confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_detect_low_risk_access_intent(self, agent: IntentDetectionAgent) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"intent": "low_risk_access", "confidence": 0.9, "entities": {"resource_type": "jira", "access_level": "read"}, "reasoning": "Read access request"}'))]
        with patch.object(agent.llm.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            result = await agent.detect("I need read access to Jira project OPS")
            assert result["intent"] == IntentType.LOW_RISK_ACCESS

    @pytest.mark.asyncio
    async def test_detect_high_risk_access_intent(self, agent: IntentDetectionAgent) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"intent": "high_risk_access", "confidence": 0.92, "entities": {"resource_type": "production_database", "access_level": "admin"}, "reasoning": "Production database admin access"}'))]
        with patch.object(agent.llm.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            result = await agent.detect("I need admin access to the production database")
            assert result["intent"] == IntentType.HIGH_RISK_ACCESS

    @pytest.mark.asyncio
    async def test_detect_handles_llm_failure(self, agent: IntentDetectionAgent) -> None:
        with patch.object(agent.llm.chat.completions, 'create', new_callable=AsyncMock, side_effect=Exception("API error")):
            result = await agent.detect("test message")
            assert result["intent"] == IntentType.UNKNOWN
