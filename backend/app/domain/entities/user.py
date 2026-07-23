from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class User(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    email: str
    display_name: str
    department: str = ""
    role: str = "user"
    teams: list[str] = Field(default_factory=list)
    manager_id: uuid.UUID | None = None
    azure_ad_id: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
