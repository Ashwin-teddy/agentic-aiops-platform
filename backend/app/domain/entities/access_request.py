from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums.access import AccessType, ResourceType
from app.domain.enums.status import TaskStatus
from app.domain.enums.risk import RiskLevel


class AccessRequest(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    resource_type: ResourceType
    resource_identifier: str
    access_type: AccessType
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: float = 0.0
    justification: str = ""
    status: TaskStatus = TaskStatus.PENDING
    manager_approval_id: uuid.UUID | None = None
    security_approval_id: uuid.UUID | None = None
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
