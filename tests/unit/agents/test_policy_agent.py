import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.policy.policy_agent import PolicyAgent
from app.domain.enums.risk import RiskLevel


class TestPolicyAgent:
    @pytest.fixture
    def agent(self) -> PolicyAgent:
        agent = PolicyAgent()
        agent.org_memory.get_policy = AsyncMock(return_value=None)
        return agent

    @pytest.mark.asyncio
    async def test_low_risk_jira_read(self, agent: PolicyAgent) -> None:
        result = await agent.evaluate_risk("jira", "read")
        assert result["risk_level"] == RiskLevel.LOW
        assert result["auto_approve"] is True
        assert result["requires_approval"] is False

    @pytest.mark.asyncio
    async def test_high_risk_aws_admin(self, agent: PolicyAgent) -> None:
        result = await agent.evaluate_risk("aws_iam", "admin")
        assert result["risk_level"] == RiskLevel.CRITICAL
        assert result["requires_approval"] is True
        assert result["requires_security_approval"] is True

    @pytest.mark.asyncio
    async def test_medium_risk_github_write(self, agent: PolicyAgent) -> None:
        result = await agent.evaluate_risk("github", "write")
        assert result["risk_level"] in (RiskLevel.LOW, RiskLevel.MEDIUM)

    @pytest.mark.asyncio
    async def test_high_risk_kubernetes_admin(self, agent: PolicyAgent) -> None:
        result = await agent.evaluate_risk("kubernetes", "admin")
        assert result["risk_level"] == RiskLevel.CRITICAL
        assert result["requires_approval"] is True

    @pytest.mark.asyncio
    async def test_context_adjusts_risk(self, agent: PolicyAgent) -> None:
        result_without = await agent.evaluate_risk("github", "write")
        result_with = await agent.evaluate_risk("github", "write", user_context={"is_on_team": True})
        assert result_with["risk_score"] <= result_without["risk_score"]
