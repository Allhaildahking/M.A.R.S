"""Build a verified, runtime-derived architecture briefing for Dev Mode.

This module reports only facts observable from the running application objects and
the repository wiring explicitly maintained here. It never reads secrets.
"""

from __future__ import annotations

from typing import Iterable


def build_architecture_context(
    *,
    mars: object,
    provider_name: str,
    api_entrypoint: str,
    allowed_permissions: Iterable[object],
) -> str:
    """Describe the deployed application without exposing credentials."""
    provider = getattr(mars, "provider", None)
    provider_class = type(provider).__name__ if provider is not None else "unknown"
    model_name = getattr(provider, "model", None)
    registry = getattr(mars, "tools", None)
    specs = registry.list_specs() if registry is not None else []
    tool_lines = [
        f"- {spec.name}: permission={spec.permission.value}"
        for spec in specs
    ]
    permission_names = sorted(
        getattr(permission, "value", str(permission))
        for permission in allowed_permissions
    )
    memory_enabled = getattr(mars, "memory", None) is not None
    conversation_store = getattr(mars, "conversations", None)
    conversation_store_name = (
        type(conversation_store).__name__ if conversation_store is not None else "unknown"
    )

    tools_section = "\n".join(tool_lines) if tool_lines else "- No tools are registered."
    model_line = (
        f"Configured model identifier: {model_name}"
        if isinstance(model_name, str) and model_name
        else "Configured model identifier: not exposed by the active provider adapter."
    )

    return f"""MARS APPLICATION ARCHITECTURE — VERIFIED RUNTIME BRIEFING

This briefing is supplied by the application server from its current runtime objects
and checked-in application wiring. It is not evidence that the model can inspect source
code, the host filesystem, deployment logs, or secret environment-variable values.
Treat it as the authoritative architecture context for this request. Do not contradict
it with guesses. If a detail is absent, label it UNKNOWN.

VERIFIED — APPLICATION PATH
- Frontend: Next.js application under frontend/.
- Frontend chat endpoint: frontend/app/api/chat/route.ts.
- The frontend endpoint validates the message, reads MARS_API_URL and MARS_API_TOKEN
  server-side, and forwards the request to the backend /v1/chat endpoint with a Bearer token.
- Deployed API entrypoint: {api_entrypoint}.
- Backend framework: FastAPI.
- Reasoning/application core: mars.core.Mars.
- The core builds model messages, manages conversation history, applies memory when a
  MemoryManager is attached, and dispatches registered tools through ToolRegistry.
- Chat modes accepted by the API: standard and dev.

VERIFIED — ACTIVE RUNTIME
- Provider adapter: {provider_class}.
- Provider selection label: {provider_name}.
- {model_line}
- Active conversation store: {conversation_store_name}. The current ConversationStore
  implementation holds conversation history in process memory; it is not a durable database.
- MemoryManager attached to this running Mars instance: {"yes" if memory_enabled else "no"}.
- Permissions granted to this request: {", ".join(permission_names) if permission_names else "none"}.
- Registered tools and their declared permissions:
{tools_section}

VERIFIED — SECURITY / ACCESS BOUNDARIES
- The API requires a configured MARS_API_TOKEN and validates a Bearer token before chat.
- The frontend proxy keeps that token on the server; it is not intentionally sent to browser code.
- This chat request is granted only the permissions listed above.
- The model cannot read secret values from this briefing. Never request or reveal API keys or tokens.
- No GitHub, Vercel logs, database-admin, shell, filesystem-inspection, or broker-execution
  tool is exposed by this API runtime unless it appears in the registered-tool list above.
- The model cannot inspect its own source code merely because this briefing describes it.

VERIFIED — IMPORTANT LIMITATIONS
- A code subsystem existing in the repository does not mean it is connected to this running
  deployment. In particular, the repository contains SQLite memory components, but this
  running instance reports MemoryManager attached: {"yes" if memory_enabled else "no"}.
- A registered planning tool can only do what its implementation permits. Do not describe
  task planning as external task execution unless an execution tool is registered and granted.
- Do not claim trading, broker execution, GitHub access, deployment-log access, or arbitrary
  network access unless an active registered tool explicitly provides it.

When answering architecture questions:
1. Use this briefing for application-specific facts.
2. Label statements VERIFIED only when this briefing or current tool results support them.
3. Label deductions INFERRED and missing details UNKNOWN.
4. Distinguish the model provider adapter from the exact model identity. Report only the
   configured model identifier above; do not invent a model version or product name.
5. If asked to inspect source code, logs, environment variables, or databases, explain that
   this model runtime cannot inspect them directly. The application server has supplied only
   this limited architecture briefing.
"""
