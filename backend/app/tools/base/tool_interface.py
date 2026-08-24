from __future__ import annotations

import time
from abc import abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.core.security.encryption import mask_pii
from app.observability.logging import get_logger

logger = get_logger(__name__)


class ToolResult(BaseModel):
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0


class BaseTool:
    name: str = "base_tool"
    description: str = "Base tool"
    category: str = "general"
    required_permissions: list[str] = Field(default_factory=list)
    risk_score: float = 0.0
    timeout_seconds: int = 30

    def __init__(self) -> None:
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("tool_initialized", tool=self.name)

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult: ...

    @abstractmethod
    async def validate_params(self, **kwargs: Any) -> bool: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    async def safe_execute(self, **kwargs: Any) -> ToolResult:
        start = time.monotonic()
        try:
            if not self._initialized:
                await self.initialize()
            if not await self.validate_params(**kwargs):
                return ToolResult(
                    success=False,
                    error="Invalid parameters",
                    metadata={"tool": self.name},
                )
            sanitized_kwargs = {
                k: mask_pii(str(v)) if isinstance(v, str) else v for k, v in kwargs.items()
            }
            logger.info(
                "tool_execution_started", tool=self.name, params_keys=list(sanitized_kwargs.keys())
            )
            result = await self.execute(**kwargs)
            elapsed_ms = (time.monotonic() - start) * 1000
            result.execution_time_ms = elapsed_ms
            result.metadata["tool"] = self.name
            result.metadata["execution_time_ms"] = elapsed_ms
            logger.info(
                "tool_execution_completed", tool=self.name, success=result.success, ms=elapsed_ms
            )
            return result
        except Exception as e:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error("tool_execution_failed", tool=self.name, error=str(e), ms=elapsed_ms)
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=elapsed_ms,
                metadata={"tool": self.name, "error_type": type(e).__name__},
            )

    def to_langchain_tool(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "risk_score": self.risk_score,
            "required_permissions": self.required_permissions,
        }
