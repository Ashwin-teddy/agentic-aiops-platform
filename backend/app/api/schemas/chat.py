from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    session_id: str | None = Field(None, description="Existing session ID")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    channels: list[str] = Field(default_factory=lambda: ["slack"], description="Notification channels")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    intent: str = ""
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    requires_approval: bool = False
    approval_id: str | None = None
