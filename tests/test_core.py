from dataclasses import dataclass

from mars.core import Mars, Message
from mars.memory import MemoryManager, SQLiteMemoryStore
from mars.providers import EchoProvider
from mars.tools import ModelTurn, ToolCall, ToolPermission, ToolResult, ToolSpec


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


class AgentProvider:
    def __init__(self, turns: list[ModelTurn]) -> None:
        self.turns = iter(turns)
        self.seen_messages: list[list[Message]] = []

    def generate(self, messages: list[Message]) -> str:
        return "fallback"

    def generate_turn(
        self,
        messages: list[Message],
        tool_specs: list[dict[str, object]],
    ) -> ModelTurn:
        self.seen_messages.append(messages)
        return next(self.turns)


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


def test_mars_runs_model_selected_tool_then_reasons_again() -> None:
    provider = AgentProvider(
        [
            ModelTurn(tool_calls=(ToolCall(name="echo", arguments={"text": "hello"}),)),
            ModelTurn(text="The tool returned hello."),
        ]
    )
    mars = Mars(provider)
    mars.tools.register(EchoTool())

    result = mars.respond(
        "Use the echo tool.",
        allowed_permissions={ToolPermission.READ},
    )

    assert result == "The tool returned hello."
    assert any("Tool result for echo" in message.content for message in provider.seen_messages[1])


def test_mars_returns_permission_denial_to_the_model() -> None:
    provider = AgentProvider(
        [
            ModelTurn(tool_calls=(ToolCall(name="echo", arguments={"text": "hello"}),)),
            ModelTurn(text="I could not run that tool without permission."),
        ]
    )
    mars = Mars(provider)
    mars.tools.register(EchoTool())

    result = mars.respond("Use the echo tool.")

    assert result == "I could not run that tool without permission."
    assert "Permission denied" in provider.seen_messages[1][-1].content


def test_mars_stops_runaway_tool_loops() -> None:
    provider = AgentProvider(
        [ModelTurn(tool_calls=(ToolCall(name="echo", arguments={"text": "loop"}),))]
    )
    mars = Mars(provider, max_tool_rounds=2)
    mars.tools.register(EchoTool())

    result = mars.respond(
        "Keep using the echo tool.",
        allowed_permissions={ToolPermission.READ},
    )

    assert "safety limit" in result
