from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.schemas.access import AccessRequestCreate, AccessRequestResponse
from app.agents.access_management.access_agent import AccessManagementAgent
from app.agents.policy.policy_agent import PolicyAgent
from app.agents.human_approval.approval_agent import HumanApprovalAgent
from app.domain.enums.risk import RiskLevel
from app.integrations.google_drive import drive_service
from app.observability.logging import get_logger

router = APIRouter(prefix="/access", tags=["Access Management"])
logger = get_logger(__name__)

access_agent = AccessManagementAgent()
policy_agent = PolicyAgent()
approval_agent = HumanApprovalAgent()


@router.post("/request", response_model=AccessRequestResponse)
async def create_access_request(
    request: AccessRequestCreate,
    current_user: CurrentUser = Depends(get_current_user),
) -> AccessRequestResponse:
    risk_eval = await policy_agent.evaluate_risk(
        resource_type=request.resource_type,
        access_type=request.access_type,
        user_context={"justification": request.justification},
    )
    risk_level = RiskLevel(risk_eval["risk_level"])
    needs_approval = request.resource_type == "google_drive" or not risk_eval.get("auto_approve", False)
    result = await access_agent.process_access_request(
        user_id=current_user.user_id,
        resource_type=request.resource_type,
        resource_identifier=request.resource_identifier,
        access_type=request.access_type,
        risk_level=risk_level,
        justification=request.justification,
        auto_execute=not needs_approval,
    )
    if needs_approval:
        approval = await approval_agent.create_approval_request(
            request_id=result["request_id"],
            requester_id=current_user.user_id,
            requester_email=current_user.email,
            resource_type=request.resource_type,
            resource_identifier=request.resource_identifier,
            access_type=request.access_type,
            risk_level=risk_level,
            risk_score=risk_eval["risk_score"],
            justification=request.justification,
        )
        result["approval_id"] = approval["approval_id"]
        result["message"] = "Access request submitted for approval"
    return AccessRequestResponse(**result)


@router.get("/pending")
async def get_pending_requests(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    approvals = await approval_agent.get_pending_approvals_for_user(current_user.user_id)
    return approvals


@router.post("/approve/{approval_id}")
async def approve_request(
    approval_id: str,
    decision: str = "approved",
    comments: str = "",
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    current_user.require_permission(ApprovalPermission)
    result = await approval_agent.submit_approval(
        approval_id=approval_id,
        approver_id=current_user.user_id,
        decision=decision,
        comments=comments,
    )
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    approval = result["approval"]
    if approval.get("status") == "approved" and approval.get("resource_type") == "google_drive":
        share_result = await drive_service.share_with_user(
            user_id=current_user.user_id,
            resource_identifier=approval.get("resource_identifier", ""),
            email=approval.get("requester_email", ""),
            access_type=approval.get("access_type", "read"),
        )
        result["share_result"] = share_result
    return result


from app.core.security.rbac import Permission as ApprovalPermission
