"""End-to-end tests for web research through the MARS reasoning loop."""

from mars.core import Mars, Message
from mars.tools import (
    ModelTurn,
    ToolCall,
    ToolPermission,
    ToolRegistry,
)
from mars.tools.research import WebFetchTool, WebSearchTool


class ScriptedResearchProvider:
    """Deterministic model substitute for testing tool orchestration."""

    def __init__(self, turns: list[ModelTurn]) -> None:
        self.turns = iter(turns)
        self.seen_messages: list[list[Message]] = []
        self.seen_tool_specs: list[list[dict[str, object]]] = []

    def generate(self, messages: list[Message]) -> str:
        return "fallback"

    def generate_turn(
        self,
        messages: list[Message],
        tool_specs: list[dict[str, object]],
    ) -> ModelTurn:
        self.seen_messages.append(list(messages))
        self.seen_tool_specs.append(tool_specs)
        return next(self.turns)


def test_mars_completes_search_fetch_and_source_cited_answer() -> None:
    search_calls: list[tuple[str, int]] = []
    fetch_calls: list[str] = []

    def searcher(query: str, limit: int) -> list[dict[str, str]]:
        search_calls.append((query, limit))
        return [
            {
                "title": "Official Battery Report",
                "href": "https://example.com/battery-report",
                "body": "A report about battery recycling.",
            }
        ]

    def fetcher(url: str) -> dict[str, str]:
        fetch_calls.append(url)
        return {
            "title": "Official Battery Report",
            "url": url,
            "content": "The report describes battery recycling methods.",
        }

    provider = ScriptedResearchProvider(
        [
            ModelTurn(
                tool_calls=(
                    ToolCall(
                        name="web_search",
                        arguments={"query": "battery recycling report", "max_results": 3},
                    ),
                )
            ),
            ModelTurn(
                tool_calls=(
                    ToolCall(
                        name="web_fetch",
                        arguments={"url": "https://example.com/battery-report"},
                    ),
                )
            ),
            ModelTurn(
                text=(
                    "The report describes battery recycling methods. "
                    "Source: https://example.com/battery-report"
                )
            ),
        ]
    )
    registry = ToolRegistry()
    registry.register(WebSearchTool(searcher=searcher))
    registry.register(WebFetchTool(fetcher=fetcher))
    mars = Mars(provider=provider, tools=registry)

    answer = mars.respond(
        "Research battery recycling and cite your source.",
        allowed_permissions={ToolPermission.READ},
    )

    assert "Source: https://example.com/battery-report" in answer
    assert search_calls == [("battery recycling report", 3)]
    assert fetch_calls == ["https://example.com/battery-report"]
    assert len(provider.seen_messages) == 3
    assert "Official Battery Report" in str(provider.seen_messages[1])
    assert "battery recycling methods" in str(provider.seen_messages[2])
    exposed_tools = {spec["name"] for spec in provider.seen_tool_specs[0]}
    assert exposed_tools == {"web_search", "web_fetch"}


def test_mars_research_permission_denial_does_not_call_searcher() -> None:
    search_calls = 0

    def searcher(query: str, limit: int) -> list[dict[str, str]]:
        nonlocal search_calls
        search_calls += 1
        return []

    provider = ScriptedResearchProvider(
        [
            ModelTurn(
                tool_calls=(
                    ToolCall(name="web_search", arguments={"query": "battery recycling"}),
                )
            ),
            ModelTurn(text="I need read permission to search the web."),
        ]
    )
    registry = ToolRegistry()
    registry.register(WebSearchTool(searcher=searcher))
    mars = Mars(provider=provider, tools=registry)

    answer = mars.respond("Search for battery recycling.")

    assert "read permission" in answer
    assert search_calls == 0
    assert "Permission denied" in provider.seen_messages[1][-1].content
