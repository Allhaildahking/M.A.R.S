"""Rules and model-assisted extraction for persistent memory."""

from dataclasses import dataclass
from typing import Protocol

from google import genai
from google.genai import types
from pydantic import BaseModel

from ..config import settings


@dataclass(frozen=True)
class MemoryCandidate:
    """A proposed persistent memory."""

    content: str
    category: str = "general"


class MemoryDecision(BaseModel):
    """Structured decision returned by a memory extractor."""

    should_remember: bool
    content: str = ""
    category: str = "general"


class MemoryExtractor(Protocol):
    def extract(self, message: str) -> MemoryCandidate | None:
        """Propose a memory from a user message."""


class MemoryFormation:
    """Deterministic extraction for explicit remember requests."""

    _PREFIXES = (
        "remember that ",
        "remember this: ",
        "remember this ",
        "don't forget that ",
        "dont forget that ",
    )

    def extract(self, message: str) -> MemoryCandidate | None:
        normalized = message.strip()
        lowered = normalized.lower()

        for prefix in self._PREFIXES:
            if lowered.startswith(prefix):
                content = normalized[len(prefix):].strip()
                if content:
                    return MemoryCandidate(content=content, category="explicit")

        return None


class GeminiMemoryExtractor:
    """Uses Gemini structured output to propose durable memories."""

    _PROMPT = """Decide whether the user's message contains a useful, durable fact,
preference, project detail, instruction, or goal that should be remembered across
future conversations.

Do not remember secrets, passwords, API keys, authentication codes, financial
credentials, or highly sensitive personal information.

If nothing durable is present, set should_remember to false.
If it is worth remembering, rewrite it as one concise factual statement and choose
a category: preference, project, goal, instruction, context, or general.

User message:
"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: genai.Client | None = None,
    ) -> None:
        self.model = model or settings.gemini_model
        self.client = client or genai.Client(api_key=api_key or settings.gemini_api_key)

    def extract(self, message: str) -> MemoryCandidate | None:
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{self._PROMPT}{message}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MemoryDecision,
            ),
        )

        decision = response.parsed
        if not isinstance(decision, MemoryDecision) or not decision.should_remember:
            return None

        content = decision.content.strip()
        if not content:
            return None

        return MemoryCandidate(content=content, category=decision.category)
