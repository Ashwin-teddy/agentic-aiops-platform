import pytest
from app.agents.audit.audit_agent import AuditAgent


class TestAuditAgent:
    @pytest.fixture
    def agent(self) -> AuditAgent:
        return AuditAgent()

    @pytest.mark.asyncio
    async def test_log_action(self, agent: AuditAgent) -> None:
        entry = await agent.log_action(
            user_id="user-1",
            session_id="session-1",
            action="test.action",
            success=True,
        )
        assert entry["user_id"] == "user-1"
        assert entry["action"] == "test.action"
        assert entry["success"] is True

    @pytest.mark.asyncio
    async def test_get_audit_trail(self, agent: AuditAgent) -> None:
        await agent.log_action(user_id="user-1", session_id="s1", action="a.b")
        await agent.log_action(user_id="user-2", session_id="s1", action="c.d")
        trail = await agent.get_audit_trail(user_id="user-1")
        assert len(trail) == 1

    @pytest.mark.asyncio
    async def test_security_event(self, agent: AuditAgent) -> None:
        entry = await agent.log_security_event(
            user_id="user-1",
            event_type="unauthorized_access",
            details={"target": "prod-db"},
            ip_address="10.0.0.1",
        )
        assert "security.unauthorized_access" in entry["action"]
