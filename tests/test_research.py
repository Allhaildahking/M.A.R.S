from mars.tools import ToolPermission, ToolRegistry, ToolResult
from mars.tools.research import (
    WebFetchTool,
    WebSearchTool,
    _ReadableHTML,
    _validate_public_url,
    register_web_research_tools,
)


def test_search_returns_source_urls_and_snippets() -> None:
    tool = WebSearchTool(
        searcher=lambda query, limit: [
            {"title": "Official page", "href": "https://example.com/docs", "body": "Useful details"}
        ]
    )

    result = tool.execute({"query": "example docs", "max_results": 3})

    assert result.success
    assert result.output == {
        "query": "example docs",
        "result_count": 1,
        "results": [
            {
                "title": "Official page",
                "url": "https://example.com/docs",
                "snippet": "Useful details",
            }
        ],
    }


def test_search_rejects_invalid_query_and_result_count() -> None:
    tool = WebSearchTool(searcher=lambda query, limit: [])

    assert not tool.execute({"query": " "}).success
    assert not tool.execute({"query": "ok", "max_results": 99}).success


def test_search_errors_are_returned_safely() -> None:
    def fail(query: str, limit: int) -> list[dict[str, str]]:
        raise TimeoutError("provider timed out")

    result = WebSearchTool(searcher=fail).execute({"query": "latest science"})

    assert not result.success
    assert "Web search failed" in (result.error or "")


def test_fetch_tool_returns_page_content() -> None:
    expected = {
        "title": "Example",
        "url": "https://example.com",
        "content": "Readable page text",
    }
    tool = WebFetchTool(fetcher=lambda url: expected)

    result = tool.execute({"url": "https://example.com"})

    assert result == ToolResult(success=True, output=expected)


def test_fetch_tool_handles_fetch_failure() -> None:
    def fail(url: str) -> dict[str, str]:
        raise ValueError("blocked")

    result = WebFetchTool(fetcher=fail).execute({"url": "https://example.com"})

    assert not result.success
    assert "Web page fetch failed" in (result.error or "")


def test_private_and_non_http_urls_are_rejected() -> None:
    for url in (
        "http://127.0.0.1/admin",
        "http://192.168.1.10/",
        "file:///etc/passwd",
        "http://localhost/",
    ):
        try:
            _validate_public_url(url)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected URL to be rejected: {url}")


def test_html_extraction_omits_scripts_and_styles() -> None:
    parser = _ReadableHTML()
    parser.feed(
        "<html><head><title>Good title</title><style>hidden style</style></head>"
        "<body><p>Useful text</p><script>ignore this</script></body></html>"
    )

    assert "Good title" in " ".join(parser.title_parts)
    text = " ".join(parser.text_parts)
    assert "Useful text" in text
    assert "ignore this" not in text
    assert "hidden style" not in text


def test_web_research_tools_register_as_read_only() -> None:
    registry = ToolRegistry()
    register_web_research_tools(registry)

    specs = {spec.name: spec for spec in registry.list_specs()}
    assert set(specs) == {"web_search", "web_fetch"}
    assert specs["web_search"].permission == ToolPermission.READ
    assert specs["web_fetch"].permission == ToolPermission.READ


def test_web_search_requires_read_permission_through_registry() -> None:
    registry = ToolRegistry()
    registry.register(WebSearchTool(searcher=lambda query, limit: []))

    result = registry.execute("web_search", {"query": "testing"})
    assert not result.success
    assert "Permission denied" in (result.error or "")
