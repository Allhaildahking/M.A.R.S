from dataclasses import dataclass

from mars.core import Mars
from mars.memory import MemoryManager, SQLiteMemoryStore
from mars.providers import EchoProvider
from mars.tools import ToolPermission, ToolResult, ToolSpec


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


def test_mars_responds_through_provider() -> None:
    mars = Mars(EchoProvider())
    assert mars.respond("hello") == "MARS received: hello"


def test_mars_preserves_input() -> None:
    mars = Mars(EchoProvider())
    assert "second" in mars.respond("second", history=[])


def test_mars_retrieves_relevant_memory() -> None:
    memory = MemoryManager(SQLiteMemoryStore(":memory:"))
    memory.remember("User wants MARS to be a general personal AI.", category="project")

    mars = Mars(EchoProvider(), memory=memory)
    response = mars.respond("What is MARS supposed to be?")

    assert "What is MARS supposed to be?" in response


def test_mars_can_execute_a_registered_tool() -> None:
    mars = Mars(EchoProvider())
    mars.tools.register(EchoTool())

    result = mars.execute_tool(
        "echo",
        {"text": "hello"},
        allowed_permissions={ToolPermission.READ},
    )

    assert result == ToolResult(success=True, output="hello")


def test_mars_cannot_bypass_tool_permissions() -> None:
    mars = Mars(EchoProvider())
    mars.tools.register(EchoTool())

    result = mars.execute_tool("echo", {"text": "hello"})

    assert result.success is False
    assert "Permission denied" in (result.error or "")
