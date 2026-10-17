# MARS

MARS — Multifunctional Autonomous Reasoning System

> **Project provenance:** Copyright (c) 2026 Destiny Growrich.  
> **Provenance marker:** `MARS-DG-2026`  
> **Canonical repository:** github.com/Allhaildahking/M.A.R.S

MARS is a modular personal AI system built to reason, remember, write, code, research, analyze markets, and eventually execute tasks through controlled tools.

Stage: Foundation / v0.1

Core principles:
- Modular over monolithic
- Model-agnostic where practical
- Memory is explicit and controllable
- Tools require defined permissions
- Trading execution is isolated behind risk controls
- Every capability should be independently testable
- Security and observability are part of the foundation

## Implemented capabilities

- Structured model-driven tool loop with permission enforcement
- Long-term memory and short-term conversation sessions
- Read-only web search returning titles, snippets, and source URLs
- Public web-page retrieval with readable text extraction and content limits
- Network safety checks that reject private/local hosts and unsafe redirects
- End-to-end automated tests for search, page retrieval, and source-cited responses

## Planned capabilities

- Writing and document assistance
- Software development tools
- Market analysis
- Controlled trading execution
- Task planning and automation
- Telegram/web interfaces
- Scheduled workflows

## Run locally

Development target: Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows, activate the environment with `.venv\\Scripts\\activate`.

Set `GEMINI_API_KEY` in your environment before using `GeminiProvider`. Never commit API keys to the repository.

### Run a live research smoke test

This calls the configured Gemini model and the live web search service. It may use API quota and requires an internet connection.

Linux/macOS:

```bash
export GEMINI_API_KEY="your-key"
python scripts/smoke_test_research.py
```

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY = "your-key"
python scripts/smoke_test_research.py
```

You can provide a custom research question:

```bash
python scripts/smoke_test_research.py "Find a recent official NASA Artemis update"
```

The script never prints the API key. It returns a non-zero exit code if the key is missing, the live request fails, the answer is empty, or the answer contains no source URLs. A passing run verifies a live answer with source links, but does not guarantee that every fact is correct.

### Use web research in your own code

```python
from mars.core import Mars
from mars.providers import GeminiProvider
from mars.tools import ToolPermission, ToolRegistry, register_web_research_tools

tools = ToolRegistry()
register_web_research_tools(tools)

mars = Mars(provider=GeminiProvider(), tools=tools)
answer = mars.respond(
    "Research recent developments in battery recycling and compare reliable sources.",
    allowed_permissions={ToolPermission.READ},
)
print(answer)
```

The caller must explicitly grant read permission before MARS can use web tools.

License will be chosen before the first public release.
