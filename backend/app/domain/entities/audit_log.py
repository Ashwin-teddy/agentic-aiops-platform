from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLog(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    session_id: str = ""
    action: str
    resource_type: str = ""
    resource_id: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    ip_address: str = ""
    user_agent: str = ""
    risk_score: float = 0.0
    success: bool = True
    error_message: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
