from types import SimpleNamespace

from mars.core import Message
from mars.providers import AgentResponse, GeminiProvider
from mars.tools import ToolCall


class FakeModels:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(text=self.response_text)


class FakeClient:
    def __init__(self, response_text: str) -> None:
        self.models = FakeModels(response_text)


def test_gemini_provider_sends_system_messages_as_system_instruction() -> None:
    client = FakeClient("Hello from Gemini")
    provider = GeminiProvider(model="test-model", client=client)  # type: ignore[arg-type]

    answer = provider.generate(
        [
            Message(role="system", content="You are MARS."),
            Message(role="user", content="Hello."),
        ]
    )

    call = client.models.calls[0]
    assert answer == "Hello from Gemini"
    assert call["config"].system_instruction == "You are MARS."
    assert [item.role for item in call["contents"]] == ["user"]
    assert call["contents"][0].parts[0].text == "Hello."


def test_gemini_structured_turn_keeps_system_instruction_out_of_chat() -> None:
    client = FakeClient(
        '{"text":"Found an answer.","tool_calls":[{"name":"web_search",'
        '"arguments":{"query":"MARS project"}}]}'
    )
    provider = GeminiProvider(model="test-model", client=client)  # type: ignore[arg-type]

    turn = provider.generate_turn(
        [
            Message(role="system", content="You are MARS."),
            Message(role="user", content="Research MARS."),
        ],
        [
            {
                "name": "web_search",
                "description": "Search the public web.",
                "permission": "read",
                "input_schema": {"type": "object"},
            }
        ],
    )

    call = client.models.calls[0]
    instruction = call["config"].system_instruction
    assert "You are MARS." in instruction
    assert "Available tools" in instruction
    assert "web_search" in instruction
    assert [item.role for item in call["contents"]] == ["user"]
    assert turn.text == "Found an answer."
    assert turn.tool_calls == (
        ToolCall(name="web_search", arguments={"query": "MARS project"}),
    )
    assert call["config"].response_mime_type == "application/json"
    assert not hasattr(call["config"], "response_schema") or call["config"].response_schema is None
