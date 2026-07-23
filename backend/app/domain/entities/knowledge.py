from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    content: str
    source: str  # "runbook", "sop", "confluence", "pdf", "incident_report", "servicenow_kb"
    source_url: str = ""
    chunk_index: int = 0
    total_chunks: int = 1
    embedding_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
