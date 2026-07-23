import pytest
from app.tools.base.tool_registry import ToolRegistry
from app.tools.base.tool_interface import BaseTool, ToolResult
from typing import Any


class MockTool(BaseTool):
    name = "mock_tool"
    description = "A mock tool for testing"

    async def execute(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, data={"echo": kwargs.get("input", "")})

    async def validate_params(self, **kwargs: Any) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


class TestToolRegistry:
    def test_register_and_get(self) -> None:
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        assert registry.get("mock_tool") is tool

    def test_get_nonexistent(self) -> None:
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_list_tools(self) -> None:
        registry = ToolRegistry()
        registry.register(MockTool())
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "mock_tool"

    def test_list_by_category(self) -> None:
        registry = ToolRegistry()
        tool = MockTool()
        tool.category = "test"
        registry.register(tool)
        assert len(registry.list_by_category("test")) == 1
        assert len(registry.list_by_category("other")) == 0


class TestMockTool:
    @pytest.mark.asyncio
    async def test_execute(self) -> None:
        tool = MockTool()
        result = await tool.safe_execute(input="hello")
        assert result.success is True
        assert result.data["echo"] == "hello"

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        tool = MockTool()
        assert await tool.health_check() is True

    def test_to_langchain_tool(self) -> None:
        tool = MockTool()
        schema = tool.to_langchain_tool()
        assert schema["name"] == "mock_tool"
