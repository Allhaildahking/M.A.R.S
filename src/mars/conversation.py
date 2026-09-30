"""Short-term conversation state for MARS.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

from dataclasses import dataclass, field

from .core import Message


@dataclass
class Conversation:
    """In-memory conversation session."""

    id: str
    messages: list[Message] = field(default_factory=list)

    def add(self, message: Message) -> None:
        self.messages.append(message)

    def history(self) -> list[Message]:
        return list(self.messages)


class ConversationStore:
    """Manage short-term conversation sessions."""

    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}

    def get_or_create(self, conversation_id: str) -> Conversation:
        if not conversation_id.strip():
            raise ValueError("conversation_id cannot be empty.")
        return self._conversations.setdefault(
            conversation_id,
            Conversation(id=conversation_id),
        )

    def get(self, conversation_id: str) -> Conversation:
        try:
            return self._conversations[conversation_id]
        except KeyError as error:
            raise KeyError(f"Unknown conversation: {conversation_id}") from error

    def delete(self, conversation_id: str) -> None:
        self._conversations.pop(conversation_id, None)
