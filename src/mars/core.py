"""Stable reasoning boundary for MARS.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

from dataclasses import dataclass
from typing import Protocol

from .instructions import MARS_SYSTEM_INSTRUCTIONS
from .memory import MemoryManager


@dataclass(frozen=True)
class Message:
    role: str
    content: str


class ModelProvider(Protocol):
    def generate(self, messages: list[Message]) -> str:
        """Generate a response from a conversation."""


class Mars:
    """Top-level application boundary."""

    def __init__(
        self,
        provider: ModelProvider,
        memory: MemoryManager | None = None,
        auto_remember: bool = False,
    ) -> None:
        self.provider = provider
        self.memory = memory
        self.auto_remember = auto_remember

    def respond(self, message: str, history: list[Message] | None = None) -> str:
        if self.memory is not None and self.auto_remember:
            self.memory.remember_if_worthwhile(message)

        messages = [
            Message(role="system", content=MARS_SYSTEM_INSTRUCTIONS),
            *(history or []),
        ]

        if self.memory is not None:
            memories = self.memory.recall(message)
            if memories:
                memory_context = "\n".join(
                    f"- [{memory.category}] {memory.content}" for memory in memories
                )
                messages.append(
                    Message(
                        role="system",
                        content=(
                            "Relevant persistent memory about the user/project:\n"
                            f"{memory_context}"
                        ),
                    )
                )

        messages.append(Message(role="user", content=message))
        return self.provider.generate(messages)
