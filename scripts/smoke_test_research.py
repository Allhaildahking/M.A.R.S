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
from mars.tools import ToolPermission, ToolRegistry, register_web_research_tools


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
    mars = Mars(
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
    if not urls:
        print("\nFAIL: Answer contains no source URLs.")
        return 1

    print(f"\nPASS: Live answer returned with {len(urls)} source URL(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
