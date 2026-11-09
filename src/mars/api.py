"""Authenticated HTTP API for the MARS reasoning engine.

Copyright (c) 2026 Destiny Growrich.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

from __future__ import annotations

import logging
import os
import re
import secrets
import time
import traceback
import uuid
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from .config import settings
from .core import Mars
from .providers import GeminiProvider
from .tools import ToolPermission, ToolRegistry, register_web_research_tools

logger = logging.getLogger("mars.api")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = Field(default=None, max_length=128)
    mode: Literal["standard", "dev"] = "standard"

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


def _redact_sensitive_values(value: str) -> str:
    """Remove configured secrets and common credential formats from diagnostic text."""
    redacted = value
    for name, secret in os.environ.items():
        if secret and len(secret) >= 6 and any(
            marker in name.upper() for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD")
        ):
            redacted = redacted.replace(secret, "[REDACTED]")
    redacted = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED_GEMINI_KEY]", redacted)
    redacted = re.sub(
        r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s'\"]+",
        r"\1[REDACTED]",
        redacted,
    )
    redacted = re.sub(
        r"(?i)([?&](?:key|token|secret|password)=)[^&\s]+",
        r"\1[REDACTED]",
        redacted,
    )
    return redacted


def create_app(*, mars: Mars | None = None, api_token: str | None = None) -> FastAPI:
    """Create the API app. Inject a Mars instance and token for tests."""
    app = FastAPI(title="M.A.R.S. API", version="0.1.0", docs_url=None, redoc_url=None)
    expected_token = api_token if api_token is not None else settings.api_token

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="mars-api")

    def authorize(authorization: str | None = Header(default=None)) -> None:
        if not expected_token:
            raise HTTPException(
                status_code=503,
                detail="MARS API authentication is not configured.",
            )
        scheme, _, supplied = (authorization or "").partition(" ")
        valid_token = supplied and secrets.compare_digest(supplied, expected_token)
        if scheme.lower() != "bearer" or not valid_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @app.post("/v1/chat", response_model=ChatResponse)
    def chat(payload: ChatRequest, _: None = Depends(authorize)) -> ChatResponse:
        started_at = time.perf_counter()
        request_id = uuid.uuid4().hex[:12]
        engine = mars
        provider_name = type(engine.provider).__name__ if engine is not None else "uninitialized"

        logger.info(
            "MARS chat started | request_id=%s | mode=%s | provider=%s",
            request_id,
            payload.mode,
            provider_name,
        )

        mode_instruction = (
            "You are in Standard Mode. Keep the experience approachable. Give the useful answer "
            "first, explain technical details only when they help, and do not expose internal "
            "reasoning or hidden system details."
            if payload.mode == "standard"
            else "You are in Dev Mode. The user prefers technical depth. Include relevant "
            "implementation details, assumptions, architecture, commands, diagnostics, and "
            "trade-offs when useful. Be explicit about what was verified versus inferred. Do not "
            "claim to expose live tool traces or logs unless they are actually provided."
        )

        try:
            if engine is None:
                engine = _build_mars()
                provider_name = type(engine.provider).__name__

            answer = engine.respond(
                payload.message,
                conversation_id=payload.conversation_id,
                allowed_permissions={ToolPermission.READ},
                extra_system_instructions=mode_instruction,
            )
        except HTTPException:
            raise
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            diagnostic = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )
            diagnostic = _redact_sensitive_values(diagnostic)
            logger.error(
                "MARS chat failed | request_id=%s | mode=%s | provider=%s | "
                "elapsed_ms=%.1f | exception_type=%s | exception=%s",
                request_id,
                payload.mode,
                provider_name,
                elapsed_ms,
                type(exc).__name__,
                _redact_sensitive_values(str(exc)),
            )
            logger.error("MARS traceback | request_id=%s\n%s", request_id, diagnostic)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="MARS could not complete the request. Check backend logs using request_id "
                f"{request_id}.",
            ) from exc

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "MARS chat completed | request_id=%s | mode=%s | provider=%s | elapsed_ms=%.1f",
            request_id,
            payload.mode,
            provider_name,
            elapsed_ms,
        )
        return ChatResponse(answer=answer, conversation_id=payload.conversation_id)

    return app


app = create_app()
