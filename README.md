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
- Validated task-plan drafting with dependency and cycle checks
- Persistent task-plan lifecycle with dependency readiness, explicit approval gates, and step status tracking; lifecycle updates never execute external actions

## Run locally

Development target: Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows, activate the environment with `.venv\\Scripts\\activate`.

Copy `.env.example` to `.env`, then set the values needed for the features you want to use. Never commit real API keys or tokens. `GEMINI_API_KEY` is required for live Gemini responses; tests that do not make live provider calls should run without it.

Before starting the API, set a private token and your provider key in the shell:

```bash
export GEMINI_API_KEY="your-key"
export MARS_API_TOKEN="a-long-random-secret"
uvicorn mars.api:app --host 127.0.0.1 --port 8000
```

On Windows PowerShell:

```powershell
$env:GEMINI_API_KEY = "your-key"
$env:MARS_API_TOKEN = "a-long-random-secret"
uvicorn mars.api:app --host 127.0.0.1 --port 8000
```

The FastAPI health endpoint is available at `/api/health`, and chat is served at `/api/chat`. Chat requires a matching bearer token. Do not put `MARS_API_TOKEN` in a `NEXT_PUBLIC_*` variable or browser-side code.

### Run tests and inspect coverage

```bash
pytest
pytest --cov=mars --cov-report=term-missing
```

CI enforces a minimum of 80% total line coverage. The current measured baseline is 84% across 57 tests, so the threshold is below the observed baseline while still catching meaningful regressions. If the test suite changes substantially, review the threshold rather than lowering it automatically.

### Run the dashboard locally

```bash
cd frontend
npm install
npm run dev
```

The dashboard's `/api/chat` server route proxies requests to the FastAPI service and adds the bearer token on the server, so the token is not sent to browser code. Create `frontend/.env.local` with the backend base URL and the same token configured for the API:

```dotenv
MARS_API_URL=http://127.0.0.1:8000
MARS_API_TOKEN=a-long-random-secret
```

Keep these variables server-side. Never use a `NEXT_PUBLIC_*` prefix for the token. The API base URL must point directly to the FastAPI service, not back to the Next.js proxy, or requests will loop.

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

## Use task planning

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

### Track a task plan safely

`TaskPlanStore` saves plans in SQLite and tracks progress across restarts. It does not execute the work described by a step. Steps with dependencies cannot start until those dependencies are completed, and steps marked `requires_approval` cannot start until explicitly approved.

```python
from mars.tools import TaskPlanStore

with TaskPlanStore("data/mars_tasks.db") as tasks:
    plan = tasks.create_plan({
        "goal": "Prepare a portfolio launch",
        "steps": [
            {
                "id": "draft",
                "title": "Draft the launch post",
                "description": "Write the post.",
            },
            {
                "id": "publish",
                "title": "Publish the post",
                "description": "Publish after explicit approval.",
                "depends_on": ["draft"],
                "requires_approval": True,
            },
        ],
    })

    # Read ready_to_start, blocked_reason, and status for each step.
    print(plan)
    tasks.start_step(plan["id"], "draft")
    plan = tasks.complete_step(plan["id"], "draft")
    tasks.approve_step(plan["id"], "publish")
    plan = tasks.start_step(plan["id"], "publish")
```

Calling `start_step` only changes the tracked status to `in_progress`; it does not publish, send, delete, or otherwise perform the described action. External execution will need its own permission checks and action-specific approval controls.

## Use web research in your own code

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

## Planned capabilities

- Writing and document assistance
- Software development tools
- Market analysis
- Controlled trading execution
- Task execution with explicit approvals and independent permission checks
- Task planning and automation
- Telegram/web interfaces
- Scheduled workflows

License will be chosen before the first public release.

## Deploy the web dashboard and API on Vercel

The repository includes a multi-service Vercel configuration:

- `frontend`: Next.js dashboard.
- `app`: Python FastAPI service, entered through `api/index.py`.
- `/api/chat` routes to the Next.js server proxy, which adds the bearer token and forwards to the FastAPI service.
- Other `/api/*` routes, including `/api/health`, route to FastAPI; all other paths route to the dashboard.

### Vercel setup

1. Import this repository into Vercel.
2. In **Project Settings → Build and Deployment**, select **Services** as the framework.
3. Keep the repository root as the project root so Vercel can read the root `vercel.json` and `requirements.txt`.
4. Add `GEMINI_API_KEY` as a server-side environment variable on the API service if you want Gemini responses. Never add it to a `NEXT_PUBLIC_*` variable or commit it to Git.
5. Add the same strong, private `MARS_API_TOKEN` to both the API service and the frontend service's server-side environment.
6. Set `MARS_API_URL` on the frontend service to the direct URL of the FastAPI service, not the public frontend URL.
7. Deploy, then check `/api/health` on the public deployment URL and send a test message through the dashboard.

The health endpoint confirms that the API service starts. It does not verify that Gemini credentials work. Without `GEMINI_API_KEY`, the API uses the deterministic echo provider for basic connectivity checks.

The dashboard's server route proxies chat requests to the FastAPI service and keeps the bearer token out of browser code. Configure `MARS_API_URL` to the direct backend service URL and `MARS_API_TOKEN` as server-side environment variables for the frontend service. The backend must have the same token configured. Do not point `MARS_API_URL` at the public frontend URL, which can create a proxy loop. The Vercel rewrite routes `/api/chat` through the frontend proxy and other `/api/*` endpoints, including `/api/health`, to FastAPI.

Vercel Services availability and configuration can change; see the [official Vercel Services guide](https://vercel.com/kb/guide/vercel-services).
