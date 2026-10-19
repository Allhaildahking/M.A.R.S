"""Authenticated HTTP API for the MARS reasoning engine.

Copyright (c) 2026 Destiny Growrich.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

from __future__ import annotations

import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from .config import settings
from .core import Mars
from .providers import GeminiProvider
from .tools import ToolPermission, ToolRegistry, register_web_research_tools


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = Field(default=None, max_length=128)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must not be blank.")
        return value.strip()


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str


def _build_mars() -> Mars:
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MARS is not configured with a model API key.",
        )
    registry = ToolRegistry()
    register_web_research_tools(registry)
    return Mars(provider=GeminiProvider(), tools=registry)


def create_app(*, mars: Mars | None = None, api_token: str | None = None) -> FastAPI:
    """Create the API app. Inject a Mars instance and token for tests."""
    app = FastAPI(
        title="M.A.R.S. API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
    )
    expected_token = api_token if api_token is not None else settings.api_token

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="mars-api")

    def authorize(authorization: str | None = Header(default=None)) -> None:
        if not expected_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MARS API authentication is not configured.",
            )
        scheme, _, supplied = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not supplied or not secrets.compare_digest(
            supplied, expected_token
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @app.post("/v1/chat", response_model=ChatResponse)
    def chat(
        payload: ChatRequest,
        _: None = Depends(authorize),
    ) -> ChatResponse:
        engine = mars
        if engine is None:
            engine = _build_mars()
        try:
            answer = engine.respond(
                payload.message,
                conversation_id=payload.conversation_id,
                allowed_permissions={ToolPermission.READ},
            )
        except HTTPException:
            raise
        except Exception as exc:
            # Do not return provider exceptions, credentials, or internal details.
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="MARS could not complete the request. Check server logs.",
            ) from exc
        return ChatResponse(answer=answer, conversation_id=payload.conversation_id)

    return app


app = create_app()
