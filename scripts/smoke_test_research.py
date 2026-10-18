"""Run a live Gemini + web research smoke test.

Usage:
    GEMINI_API_KEY=... python scripts/smoke_test_research.py
    GEMINI_API_KEY=... python scripts/smoke_test_research.py "latest NASA Artemis update"

The API key is read from the environment and is never printed.
"""

from __future__ import annotations

import re
import sys

from mars.config import settings
from mars.core import Mars
from mars.providers import GeminiProvider
from mars.tools import ToolPermission, ToolRegistry, ToolResult, register_web_research_tools


class RecordingMars(Mars):
    """Capture tool results so the smoke test can verify real research occurred."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.tool_results: list[tuple[str, ToolResult]] = []

    def execute_tool(
        self,
        name: str,
        arguments: dict[str, object],
        *,
        allowed_permissions: set[ToolPermission] | None = None,
    ) -> ToolResult:
        result = super().execute_tool(
            name,
            arguments,
            allowed_permissions=allowed_permissions,
        )
        self.tool_results.append((name, result))
        return result


def main() -> int:
    if not settings.gemini_api_key:
        print(
            "FAIL: GEMINI_API_KEY is not set. Set it in your shell environment "
            "and run this command again."
        )
        return 2

    query = " ".join(sys.argv[1:]).strip() or (
        "Find a recent official update about NASA's Artemis program. "
        "Prefer NASA's official website."
    )
    registry = ToolRegistry()
    register_web_research_tools(registry)
    mars = RecordingMars(
        provider=GeminiProvider(),
        tools=registry,
        max_tool_rounds=5,
    )

    print(f"Question: {query}")
    print("Running live Gemini + web research test...")
    try:
        answer = mars.respond(
            query,
            allowed_permissions={ToolPermission.READ},
        )
    except Exception as error:
        print(f"FAIL: Live request raised {type(error).__name__}: {error}")
        return 1

    print("\nMARS answer:\n")
    print(answer)
    urls = re.findall(r"https?://[^\s)\]>]+", answer)
    if not answer.strip():
        print("\nFAIL: MARS returned an empty answer.")
        return 1

    search_results = [
        result.output
        for name, result in mars.tool_results
        if name == "web_search" and result.success and isinstance(result.output, dict)
    ]
    if not search_results:
        print("\nFAIL: MARS did not successfully execute web_search.")
        return 1

    source_urls = {
        str(item.get("url"))
        for result in search_results
        for item in result.get("results", [])
        if isinstance(item, dict) and item.get("url")
    }
    if not source_urls:
        print("\nFAIL: web_search returned no usable source URLs.")
        return 1

    cited_sources = {url.rstrip(".,;") for url in urls} & source_urls
    if not cited_sources:
        print("\nFAIL: Answer URLs do not match any URLs returned by web_search.")
        print(f"Search returned {len(source_urls)} source URL(s).")
        return 1

    print(
        f"\nPASS: Live answer used web_search and cited "
        f"{len(cited_sources)} URL(s) returned by the tool."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
