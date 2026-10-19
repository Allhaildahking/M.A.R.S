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
- Validated task-plan drafting with dependency and cycle checks; plan creation never executes steps

### Run the HTTP API and dashboard locally

Install the API dependencies with the development extras, then set both secrets in your shell:

```bash
export GEMINI_API_KEY="your-key"
export MARS_API_TOKEN="a-long-random-secret"
uvicorn mars.api:app --host 127.0.0.1 --port 8000
```

Set the same token in `frontend/.env.local`. These values are server-only, not browser variables:

```dotenv
MARS_API_URL=http://127.0.0.1:8000
MARS_API_TOKEN=a-long-random-secret
```

Run the dashboard from `frontend/` with `npm run dev`. The Next.js server proxies chat requests to the API, so the shared token is never sent to the browser. For a deployed dashboard, configure the same two variables in the hosting environment and point `MARS_API_URL` to an HTTPS backend. Do not use a `NEXT_PUBLIC_` prefix for the token. The chat endpoint grants read-only tool permissions; it does not enable write or execution tools.

## Planned capabilities

- Writing and document assistance
- Software development tools
- Market analysis
- Controlled trading execution
- Task execution with explicit approvals and independent permission checks
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

### Draft a validated task plan

The planning tool checks task steps, dependency references, and dependency cycles. It only returns a pending plan. It does not run steps or modify external systems.

```python
from mars.tools import CreateTaskPlanTool

result = CreateTaskPlanTool().execute(
    {
        "goal": "Prepare a portfolio launch",
        "steps": [
            {
                "id": "draft",
                "title": "Draft the launch post",
                "description": "Write the post and include the portfolio URL.",
            },
            {
                "id": "review",
                "title": "Review the post",
                "description": "Check wording and links before publishing.",
                "depends_on": ["draft"],
                "requires_approval": True,
            },
        ],
    }
)
if result.success:
    print(result.output)
```

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


## Deploy the web dashboard and API on Vercel

The repository includes a multi-service Vercel configuration:

- `frontend`: Next.js dashboard.
- `app`: Python FastAPI service, entered through `api/index.py`.
- `/api/*` routes to the Python service; all other paths route to the dashboard.

### Vercel setup

1. Import this repository into Vercel.
2. In **Project Settings → Build and Deployment**, select **Services** as the framework.
3. Keep the repository root as the project root so Vercel can read the root `vercel.json` and `requirements.txt`.
4. Add `GEMINI_API_KEY` as a server-side environment variable if you want Gemini responses. Never add it to a `NEXT_PUBLIC_*` variable or commit it to Git.
5. Add `MARS_API_TOKEN` as a strong, private bearer token. The chat endpoint returns `503` until this variable is configured and rejects requests without the matching bearer token.
6. Deploy, then check `/api/health` on the deployment URL.

The health endpoint confirms that the API service starts. It does not verify that Gemini credentials work. Without `GEMINI_API_KEY`, the API uses the deterministic echo provider for basic connectivity checks.

**Current limitation:** the dashboard is still a visual shell and does not yet send authenticated requests to `/api/chat`. Do not expose the API token in browser-side code. A server-side frontend proxy/authentication flow must be added before connecting the dashboard chat to this protected endpoint.

Vercel Services availability and configuration can change; see the [official Vercel Services guide](https://vercel.com/kb/guide/vercel-services).
