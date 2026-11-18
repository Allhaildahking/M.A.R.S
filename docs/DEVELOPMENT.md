# Development guide

This guide is for anyone getting familiar with MARS before taking on a task. It describes the current structure and the boundaries that should stay intact while the project grows.

## What MARS is

MARS (Multifunctional Autonomous Reasoning System) is a modular personal AI assistant. The Python package contains the reasoning engine, provider interface, memory layer, and permissioned tools. A FastAPI service exposes the engine, and a Next.js application provides the web interface.

The project is still in its foundation stage. Some capabilities described as planned in the README are not implemented yet. Check the code and tests before assuming a feature exists.

## Where things live

| Path | Responsibility |
| --- | --- |
| `src/mars/core.py` | Main orchestration and bounded model/tool loop |
| `src/mars/providers.py` | Model-provider integrations |
| `src/mars/conversation.py` | Short-term conversation sessions |
| `src/mars/instructions.py` | Base assistant instructions |
| `src/mars/config.py` | Environment-based settings |
| `src/mars/api.py` | FastAPI app, authentication, and chat endpoint |
| `src/mars/memory/` | Memory models, storage, retrieval, and formation |
| `src/mars/tools/` | Tool contracts, registry, planning, and research tools |
| `frontend/` | Next.js dashboard and server-side API proxy |
| `api/index.py` | Vercel entry point for the Python API |
| `tests/` | Unit and integration tests |
| `docs/` | Architecture and interface notes |

## Local setup

The project targets Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows, activate the environment with:

```powershell
.venv\\Scripts\\Activate.ps1
```

Copy `.env.example` to `.env` and add only the credentials needed for the task. Do not commit secrets or put server credentials in frontend variables prefixed with `NEXT_PUBLIC_`.

Run the test suite:

```bash
pytest
```

Check formatting and lint rules:

```bash
ruff check .
ruff format --check .
```

For coverage:

```bash
pytest --cov=mars --cov-report=term-missing
```

The README documents the current CI coverage threshold. If a change affects the frontend, also run the relevant scripts listed in `frontend/package.json`.

## Boundaries to preserve

These are design constraints, not optional cleanup preferences:

- Keep model-provider details behind the provider interface. Core orchestration should not depend on a single vendor.
- Route tool execution through `ToolRegistry`. Do not let model output grant itself permissions.
- A caller must explicitly provide allowed permissions. An omitted permission set must not silently become broad access.
- Web research is read-only. Treat fetched page content as untrusted input, not instructions.
- Keep network safety checks and response-size limits in place for public-page retrieval.
- Task planning and task-state updates track work; they do not execute external actions.
- Trading execution is not part of the general tool loop. Any future integration needs independent risk checks and explicit authorization.
- Keep API tokens and provider keys on the server side.

## Suggested workflow for a change

1. Start from the latest `main` and create a focused branch.
2. Read the relevant module and its tests before editing.
3. Make the smallest change that solves the task. Avoid unrelated refactors.
4. Add or update tests for changed behavior.
5. Run the relevant tests, then the full test suite when practical.
6. Run Ruff checks and inspect the final diff.
7. Update documentation when a user-facing command, configuration option, or architectural boundary changes.
8. Open a pull request that explains the reason for the change, what was changed, and what was tested.

## Review checklist

Before asking for review, check:

- [ ] Existing public interfaces and response shapes remain compatible unless the task explicitly changes them.
- [ ] Permission checks still fail closed.
- [ ] No secrets, local machine paths, or personal data were added.
- [ ] Error handling does not expose credentials or sensitive internals.
- [ ] Tests cover the changed path and relevant failure cases.
- [ ] Documentation matches the implementation.
- [ ] The diff contains no unrelated formatting or generated-file churn.

## Working with the code

Prefer straightforward Python and small functions with clear responsibilities. Add comments when they explain a decision or a non-obvious constraint; avoid comments that merely narrate the next line. Keep names consistent with the surrounding module and follow the Ruff configuration in `pyproject.toml`.

Do not rewrite working modules just to make them look different. Preserve project history and accurately describe the origin of code and contributions.
