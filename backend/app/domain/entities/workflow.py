from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums.risk import RiskLevel
from app.domain.enums.workflow import WorkflowState, WorkflowType


class Workflow(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    workflow_type: WorkflowType
    name: str
    description: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    required_approvals: list[str] = Field(default_factory=list)
    max_duration_seconds: int = 3600
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowExecution(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    workflow_id: uuid.UUID
    session_id: str
    user_id: uuid.UUID
    state: WorkflowState = WorkflowState.INITIATED
    context: dict[str, Any] = Field(default_factory=dict)
    steps_completed: list[str] = Field(default_factory=list)
    current_step: str = ""
    error_message: str | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    timeout_at: datetime | None = None
