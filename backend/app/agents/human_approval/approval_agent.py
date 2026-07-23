from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.domain.enums.status import ApprovalStatus, TaskStatus
from app.domain.enums.risk import RiskLevel
from app.tools.base.tool_registry import get_tool_registry
from app.observability.logging import get_logger

logger = get_logger(__name__)


class HumanApprovalAgent:
    name = "human_approval_agent"

    def __init__(self) -> None:
        self.tool_registry = get_tool_registry()
        self.pending_approvals: dict[str, dict[str, Any]] = {}
        self.approval_timeout_minutes = 60

    async def create_approval_request(
        self,
        request_id: str,
        requester_id: str,
        resource_type: str,
        access_type: str,
        risk_level: RiskLevel,
        risk_score: float,
        justification: str = "",
        required_approvers: list[str] | None = None,
    ) -> dict[str, Any]:
        approval_id = str(uuid.uuid4())
        approval = {
            "approval_id": approval_id,
            "request_id": request_id,
            "requester_id": requester_id,
            "resource_type": resource_type,
            "access_type": access_type,
            "risk_level": risk_level.value,
            "risk_score": risk_score,
            "justification": justification,
            "status": ApprovalStatus.PENDING.value,
            "required_approvers": required_approvers or [],
            "approvals_received": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=self.approval_timeout_minutes)).isoformat(),
        }
        self.pending_approvals[approval_id] = approval
        await self._send_approval_notification(approval)
        logger.info("approval_request_created", approval_id=approval_id, risk_level=risk_level.value)
        return approval

    async def submit_approval(
        self,
        approval_id: str,
        approver_id: str,
        decision: str,
        comments: str = "",
    ) -> dict[str, Any]:
        approval = self.pending_approvals.get(approval_id)
        if not approval:
            return {"success": False, "error": "Approval request not found"}
        if approval["status"] != ApprovalStatus.PENDING.value:
            return {"success": False, "error": f"Approval already {approval['status']}"}
        if datetime.fromisoformat(approval["expires_at"]) < datetime.now(timezone.utc):
            approval["status"] = ApprovalStatus.EXPIRED.value
            return {"success": False, "error": "Approval request has expired"}
        approval["approvals_received"][approver_id] = {
            "decision": decision,
            "comments": comments,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        required = set(approval["required_approvers"])
        received_approvals = {
            aid: data for aid, data in approval["approvals_received"].items()
            if data["decision"] == "approved"
        }
        if required and required.issubset(set(received_approvals.keys())):
            approval["status"] = ApprovalStatus.APPROVED.value
            approval["approved_at"] = datetime.now(timezone.utc).isoformat()
        elif any(data["decision"] == "rejected" for data in approval["approvals_received"].values()):
            approval["status"] = ApprovalStatus.REJECTED.value
            approval["rejected_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(
            "approval_decision",
            approval_id=approval_id,
            approver=approver_id,
            decision=decision,
            new_status=approval["status"],
        )
        return {"success": True, "approval": approval}

    async def check_approval_status(self, approval_id: str) -> dict[str, Any]:
        approval = self.pending_approvals.get(approval_id)
        if not approval:
            return {"found": False}
        if approval["status"] == ApprovalStatus.PENDING.value:
            if datetime.fromisoformat(approval["expires_at"]) < datetime.now(timezone.utc):
                approval["status"] = ApprovalStatus.EXPIRED.value
        return {"found": True, "approval": approval}

    async def get_pending_approvals_for_user(self, approver_id: str) -> list[dict[str, Any]]:
        pending = []
        for approval in self.pending_approvals.values():
            if approval["status"] == ApprovalStatus.PENDING.value:
                if approver_id in approval["required_approvers"] or not approval["required_approvers"]:
                    pending.append(approval)
        return pending

    async def _send_approval_notification(self, approval: dict[str, Any]) -> None:
        notification_tool = self.tool_registry.get("slack")
        if notification_tool:
            try:
                risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(
                    approval["risk_level"], "⚪"
                )
                await notification_tool.safe_execute(
                    action="send_message",
                    channel="#access-approvals",
                    text=(
                        f"{risk_emoji} *Access Approval Required*\n"
                        f"Request: {approval['request_id']}\n"
                        f"Resource: {approval['resource_type']}\n"
                        f"Access: {approval['access_type']}\n"
                        f"Risk: {approval['risk_level']} ({approval['risk_score']:.2f})\n"
                        f"Justification: {approval['justification']}\n"
                        f"Please approve/reject in the dashboard."
                    ),
                )
            except Exception as e:
                logger.error("approval_notification_failed", error=str(e))
