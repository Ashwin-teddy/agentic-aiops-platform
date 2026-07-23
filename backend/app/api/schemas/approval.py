from __future__ import annotations

from pydantic import BaseModel, Field


class ApprovalCreate(BaseModel):
    decision: str = Field(..., description="approved or rejected")
    comments: str = Field("", description="Approval comments")


class ApprovalResponse(BaseModel):
    approval_id: str
    status: str
    message: str = ""
