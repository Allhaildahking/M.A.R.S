from dataclasses import dataclass

import pytest

from mars.tools import ToolPermission, ToolRegistry, ToolResult, ToolSpec


@dataclass
class EchoTool:
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="echo",
            description="Echo text back to MARS.",
            permission=ToolPermission.READ,
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
        )

    def execute(self, arguments: dict[str, object]) -> ToolResult:
        return ToolResult(success=True, output=arguments["text"])


def test_tool_can_be_registered_and_retrieved() -> None:
    registry = ToolRegistry()
    tool = EchoTool()
    registry.register(tool)
    assert registry.get("echo") is tool
    assert registry.list_specs() == [tool.spec]


def test_duplicate_tool_names_are_rejected() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())
    with pytest.raises(ValueError, match="Tool already registered: echo"):
        registry.register(EchoTool())


def test_unknown_tool_is_rejected() -> None:
    with pytest.raises(KeyError, match="Unknown tool: missing"):
        ToolRegistry().get("missing")


def test_permission_is_required_before_execution() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())
    result = registry.execute("echo", {"text": "hello"})
    assert result.success is False
    assert "Permission denied" in (result.error or "")


def test_authorized_tool_executes() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())
    result = registry.execute(
        "echo",
        {"text": "hello"},
        allowed_permissions={ToolPermission.READ},
    )
    assert result == ToolResult(success=True, output="hello")
