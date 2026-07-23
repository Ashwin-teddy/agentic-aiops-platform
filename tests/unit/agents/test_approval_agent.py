import pytest
from app.agents.human_approval.approval_agent import HumanApprovalAgent
from app.domain.enums.risk import RiskLevel


class TestHumanApprovalAgent:
    @pytest.fixture
    def agent(self) -> HumanApprovalAgent:
        return HumanApprovalAgent()

    @pytest.mark.asyncio
    async def test_create_approval_request(self, agent: HumanApprovalAgent) -> None:
        result = await agent.create_approval_request(
            request_id="req-1",
            requester_id="user-1",
            resource_type="aws_iam",
            access_type="admin",
            risk_level=RiskLevel.HIGH,
            risk_score=0.85,
            justification="Need to update IAM policies",
            required_approvers=["manager-1"],
        )
        assert result["status"] == "pending"
        assert result["approval_id"] in agent.pending_approvals

    @pytest.mark.asyncio
    async def test_approve_request(self, agent: HumanApprovalAgent) -> None:
        approval = await agent.create_approval_request(
            request_id="req-2", requester_id="user-2",
            resource_type="jira", access_type="write",
            risk_level=RiskLevel.MEDIUM, risk_score=0.4,
            required_approvers=["manager-2"],
        )
        result = await agent.submit_approval(
            approval_id=approval["approval_id"],
            approver_id="manager-2",
            decision="approved",
            comments="Looks good",
        )
        assert result["success"] is True
        assert result["approval"]["status"] == "approved"

    @pytest.mark.asyncio
    async def test_reject_request(self, agent: HumanApprovalAgent) -> None:
        approval = await agent.create_approval_request(
            request_id="req-3", requester_id="user-3",
            resource_type="aws_iam", access_type="admin",
            risk_level=RiskLevel.CRITICAL, risk_score=0.95,
        )
        result = await agent.submit_approval(
            approval_id=approval["approval_id"],
            approver_id="security-1",
            decision="rejected",
            comments="Too risky",
        )
        assert result["success"] is True
        assert result["approval"]["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_nonexistent_approval(self, agent: HumanApprovalAgent) -> None:
        result = await agent.submit_approval("nonexistent", "user", "approved")
        assert result["success"] is False
