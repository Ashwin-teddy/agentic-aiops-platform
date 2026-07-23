from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.schemas.access import AccessRequestCreate, AccessRequestResponse
from app.agents.access_management.access_agent import AccessManagementAgent
from app.agents.policy.policy_agent import PolicyAgent
from app.agents.human_approval.approval_agent import HumanApprovalAgent
from app.domain.enums.risk import RiskLevel
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
    result = await access_agent.process_access_request(
        user_id=current_user.user_id,
        resource_type=request.resource_type,
        resource_identifier=request.resource_identifier,
        access_type=request.access_type,
        risk_level=risk_level,
        justification=request.justification,
        auto_execute=risk_eval.get("auto_approve", False),
    )
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
    return result


from app.core.security.rbac import Permission as ApprovalPermission
