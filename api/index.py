"""Vercel Python API entrypoint for M.A.R.S.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

import hmac
import os
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from mars.core import Mars
from mars.providers import EchoProvider, GeminiProvider
from mars.tools import ToolPermission, ToolRegistry, register_planning_tools, register_web_research_tools

app = FastAPI(
    title="M.A.R.S. API",
    version="0.1.0",
    description="API boundary for the M.A.R.S. personal assistant.",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    conversation_id: str | None = Field(default=None, max_length=120)


class ChatResponse(BaseModel):
    response: str
    conversation_id: str | None = None
    provider: str


def _build_mars() -> tuple[Mars, str]:
    registry = ToolRegistry()
    register_web_research_tools(registry)
    register_planning_tools(registry)

    if os.getenv("GEMINI_API_KEY"):
        return Mars(provider=GeminiProvider(), tools=registry), "gemini"
    return Mars(provider=EchoProvider(), tools=registry), "echo"


mars, provider_name = _build_mars()


def require_api_token(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Require a configured bearer token before allowing billable chat requests."""
    expected = os.getenv("MARS_API_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Chat API is not enabled. Configure MARS_API_TOKEN in the deployment environment.",
        )
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="A valid bearer token is required.")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Non-sensitive readiness check; never exposes configuration or secrets."""
    return {"status": "ok", "service": "mars-api", "provider": provider_name}


@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(require_api_token)])
def chat(payload: ChatRequest) -> ChatResponse:
    """Generate a response after explicit API authentication."""
    try:
        response = mars.respond(
            payload.message,
            conversation_id=payload.conversation_id,
            allowed_permissions={ToolPermission.READ},
        )
    except Exception as error:
        # Avoid returning provider exception details or secrets to the caller.
        raise HTTPException(status_code=502, detail="M.A.R.S. could not complete the request.") from error
    return ChatResponse(
        response=response,
        conversation_id=payload.conversation_id,
        provider=provider_name,
    )
