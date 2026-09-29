"""Model providers for MARS.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

import json
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from .config import settings
from .core import Message
from .tools import ModelTurn, ToolCall


class AgentResponse(BaseModel):
    """Structured response contract for model-driven tool selection."""

    text: str = Field(default="")
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)


class EchoProvider:
    """Deterministic provider used for local development and tests."""

    def generate(self, messages: list[Message]) -> str:
        if not messages:
            return "MARS is ready."
        return f"MARS received: {messages[-1].content}"

    def generate_turn(
        self,
        messages: list[Message],
        tool_specs: list[dict[str, object]],
    ) -> ModelTurn:
        return ModelTurn(text=self.generate(messages))


class GeminiProvider:
    """Gemini-backed model provider."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: genai.Client | None = None,
    ) -> None:
        self.model = model or settings.gemini_model
        self.client = client or genai.Client(api_key=api_key or settings.gemini_api_key)

    def _contents(self, messages: list[Message]) -> list[types.Content]:
        return [
            types.Content(
                role="model" if message.role == "assistant" else "user",
                parts=[types.Part(text=message.content)],
            )
            for message in messages
        ]

    def generate(self, messages: list[Message]) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=self._contents(messages),
        )
        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")
        return response.text

    def generate_turn(
        self,
        messages: list[Message],
        tool_specs: list[dict[str, object]],
    ) -> ModelTurn:
        prompt = (
            "You are the reasoning engine inside MARS. "
            "Decide whether an available tool is needed. "
            "Never invent a tool name. Never bypass a tool's permission level. "
            "If a tool is needed, return tool_calls with the exact tool name and JSON arguments. "
            "After tool results are supplied, use them to produce the final answer.\n\n"
            f"Available tools:\n{json.dumps(tool_specs, ensure_ascii=False)}"
        )
        contents = self._contents(
            messages + [Message(role="system", content=prompt)]
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AgentResponse,
            ),
        )
        if not response.text:
            raise RuntimeError("Gemini returned an empty structured response.")

        parsed = AgentResponse.model_validate_json(response.text)
        calls = tuple(
            ToolCall(
                name=str(call["name"]),
                arguments=dict(call.get("arguments", {})),
            )
            for call in parsed.tool_calls
            if "name" in call
        )
        return ModelTurn(text=parsed.text, tool_calls=calls)
