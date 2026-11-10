from types import SimpleNamespace

from mars.core import Message
from mars.providers import GeminiProvider
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



class SequenceModels:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(text=str(outcome))


class SequenceClient:
    def __init__(self, outcomes: list[object]) -> None:
        self.models = SequenceModels(outcomes)


def test_gemini_provider_falls_back_after_temporary_service_unavailable() -> None:
    class TemporaryProviderError(Exception):
        code = 503

    client = SequenceClient(
        [TemporaryProviderError("primary model overloaded"), "Fallback answer"]
    )
    provider = GeminiProvider(
        model="primary-model",
        fallback_model="fallback-model",
        client=client,  # type: ignore[arg-type]
    )

    answer = provider.generate([Message(role="user", content="Hello.")])

    assert answer == "Fallback answer"
    assert [call["model"] for call in client.models.calls] == [
        "primary-model",
        "fallback-model",
    ]


def test_gemini_provider_does_not_fallback_for_non_transient_errors() -> None:
    class InvalidKeyError(Exception):
        code = 401

    client = SequenceClient([InvalidKeyError("invalid API key")])
    provider = GeminiProvider(
        model="primary-model",
        fallback_model="fallback-model",
        client=client,  # type: ignore[arg-type]
    )

    try:
        provider.generate([Message(role="user", content="Hello.")])
    except InvalidKeyError:
        pass
    else:
        raise AssertionError("Authentication errors must not trigger model fallback.")

    assert [call["model"] for call in client.models.calls] == ["primary-model"]
