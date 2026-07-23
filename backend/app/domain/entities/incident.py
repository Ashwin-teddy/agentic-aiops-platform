from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums.status import IncidentSeverity, TaskStatus


class Incident(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    description: str = ""
    severity: IncidentSeverity = IncidentSeverity.P3_MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    affected_services: list[str] = Field(default_factory=list)
    root_cause: str | None = None
    remediation: str | None = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    assigned_to: uuid.UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    servicenow_id: str | None = None
    jira_id: str | None = None
