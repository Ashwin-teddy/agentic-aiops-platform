from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AccessRequestCreate(BaseModel):
    resource_type: str = Field(..., description="Resource type")
    resource_identifier: str = Field(..., description="Specific resource identifier")
    access_type: str = Field(..., description="Access level: read, write, admin")
    justification: str = Field("", description="Business justification")
    duration_hours: int = Field(8, description="Requested access duration in hours")


class AccessRequestResponse(BaseModel):
    request_id: str
    user_id: str
    resource_type: str
    resource_identifier: str
    access_type: str
    risk_level: str
    risk_score: float
    status: str
    message: str = ""
    created_at: str = ""
