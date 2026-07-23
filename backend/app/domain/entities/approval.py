from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums.status import ApprovalStatus


class Approval(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    request_id: uuid.UUID
    requester_id: uuid.UUID
    approver_id: uuid.UUID
    approval_type: str  # "manager", "security", "team_lead"
    status: ApprovalStatus = ApprovalStatus.PENDING
    comments: str = ""
    risk_score: float = 0.0
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: datetime | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
