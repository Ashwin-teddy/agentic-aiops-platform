from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    data: dict[str, Any] = {}
    error: str | None = None
    metadata: dict[str, Any] = {}


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool interface"
    required_permissions: list[str] = []

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult: ...

    @abstractmethod
    async def validate_params(self, **kwargs: Any) -> bool: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    def to_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required_permissions": self.required_permissions,
        }
