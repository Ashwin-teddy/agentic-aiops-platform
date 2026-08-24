from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.observability.logging import get_logger

if TYPE_CHECKING:
    from app.tools.base.tool_interface import BaseTool

logger = get_logger(__name__)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        logger.info("tool_registered", tool=tool.name, category=tool.category)

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        return [tool.to_langchain_tool() for tool in self._tools.values()]

    def list_by_category(self, category: str) -> list[BaseTool]:
        return [t for t in self._tools.values() if t.category == category]

    def get_high_risk_tools(self) -> list[BaseTool]:
        return [t for t in self._tools.values() if t.risk_score > 0.7]

    async def initialize_all(self) -> None:
        for tool in self._tools.values():
            if not tool._initialized:
                await tool.initialize()

    async def health_check_all(self) -> dict[str, bool]:
        results = {}
        for name, tool in self._tools.items():
            try:
                results[name] = await tool.health_check()
            except Exception:
                results[name] = False
        return results


_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
