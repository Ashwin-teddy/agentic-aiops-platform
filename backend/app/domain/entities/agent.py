from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums.status import TaskStatus


class AgentStep(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    agent_name: str
    action: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    error_message: str | None = None
    duration_ms: float | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class AgentExecution(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: str
    workflow_id: uuid.UUID | None = None
    agent_name: str
    intent: str = ""
    steps: list[AgentStep] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    total_duration_ms: float | None = None
    tokens_used: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
