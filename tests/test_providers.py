from types import SimpleNamespace

from google.genai import types

from mars.core import Message
from mars.providers import GeminiProvider
from mars.tools import ToolCall


class FakeModels:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response: object) -> None:
        self.models = FakeModels(response)


def test_gemini_provider_sends_system_messages_as_system_instruction() -> None:
    client = FakeClient(SimpleNamespace(text="Hello from Gemini", candidates=[]))
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


def test_gemini_uses_native_function_declarations_and_parses_calls() -> None:
    function_part = types.Part.from_function_call(
        name="web_search",
        args={"query": "recent AI developments", "max_results": 3},
    )
    model_content = types.Content(role="model", parts=[function_part])
    response = SimpleNamespace(
        text=None,
        candidates=[SimpleNamespace(content=model_content)],
        function_calls=[function_part.function_call],
    )
    client = FakeClient(response)
    provider = GeminiProvider(model="test-model", client=client)  # type: ignore[arg-type]

    turn = provider.generate_turn(
        [Message(role="user", content="Find recent AI news.")],
        [
            {
                "name": "web_search",
                "description": "Search the public web.",
                "permission": "read",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            }
        ],
    )

    config = client.models.calls[0]["config"]
    declaration = config.tools[0].function_declarations[0]
    assert declaration.name == "web_search"
    assert declaration.parameters_json_schema["properties"]["query"]["type"] == "string"
    assert turn.tool_calls == (
        ToolCall(
            name="web_search",
            arguments={"query": "recent AI developments", "max_results": 3},
        ),
    )
    assert turn.provider_content is model_content


def test_explicit_live_research_forces_web_search_function_call() -> None:
    function_part = types.Part.from_function_call(
        name="web_search",
        args={"query": "three recent AI developments"},
    )
    response = SimpleNamespace(
        text=None,
        candidates=[
            SimpleNamespace(
                content=types.Content(role="model", parts=[function_part])
            )
        ],
        function_calls=[function_part.function_call],
    )
    client = FakeClient(response)
    provider = GeminiProvider(model="test-model", client=client)  # type: ignore[arg-type]

    provider.generate_turn(
        [Message(role="user", content="Find three recent AI developments.")],
        [
            {
                "name": "web_search",
                "description": "Search the public web.",
                "permission": "read",
                "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}},
            },
            {
                "name": "web_fetch",
                "description": "Fetch a public page.",
                "permission": "read",
                "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}},
            },
        ],
    )

    function_config = client.models.calls[0]["config"].tool_config.function_calling_config
    assert function_config.mode == "ANY"
    assert function_config.allowed_function_names == ["web_search"]


def test_tool_result_is_returned_as_native_function_response() -> None:
    provider = GeminiProvider(
        model="test-model",
        client=FakeClient(SimpleNamespace(text="ok", candidates=[])),  # type: ignore[arg-type]
    )
    contents = provider._contents(
        [
            Message(
                role="tool",
                content="Search returned three sources.",
                tool_name="web_search",
                tool_response={"output": {"result_count": 3}},
            )
        ]
    )

    assert contents[0].role == "tool"
    function_response = contents[0].parts[0].function_response
    assert function_response.name == "web_search"
    assert function_response.response == {"output": {"result_count": 3}}


class SequenceModels:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(text=str(outcome), candidates=[])


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


def test_gemini_schema_removes_unsupported_additional_properties() -> None:
    schema = GeminiProvider._gemini_schema(
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"value": {"type": "string"}},
                }
            },
        }
    )

    assert "additionalProperties" not in schema
    assert "additionalProperties" not in schema["properties"]["nested"]
