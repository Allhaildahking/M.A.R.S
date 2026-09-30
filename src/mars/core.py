"""Stable reasoning boundary for MARS.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

from dataclasses import dataclass
from typing import Protocol

from .conversation import ConversationStore
from .instructions import MARS_SYSTEM_INSTRUCTIONS
from .memory import MemoryManager
from .tools import ModelTurn, ToolCall, ToolPermission, ToolRegistry, ToolResult


@dataclass(frozen=True)
class Message:
    role: str
    content: str


class ModelProvider(Protocol):
    def generate(self, messages: list[Message]) -> str:
        """Generate a response from a conversation."""

    def generate_turn(
        self,
        messages: list[Message],
        tool_specs: list[dict[str, object]],
    ) -> ModelTurn:
        """Generate text and optional tool calls."""


class Mars:
    """Top-level application boundary."""

    def __init__(
        self,
        provider: ModelProvider,
        memory: MemoryManager | None = None,
        auto_remember: bool = False,
        tools: ToolRegistry | None = None,
        conversation_store: ConversationStore | None = None,
        max_tool_rounds: int = 5,
    ) -> None:
        if max_tool_rounds < 1:
            raise ValueError("max_tool_rounds must be at least 1.")
        self.provider = provider
        self.memory = memory
        self.auto_remember = auto_remember
        self.tools = tools or ToolRegistry()
        self.conversations = conversation_store or ConversationStore()
        self.max_tool_rounds = max_tool_rounds

    def _build_messages(
        self,
        message: str,
        history: list[Message] | None,
    ) -> list[Message]:
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
        return messages

    def respond(
        self,
        message: str,
        history: list[Message] | None = None,
        *,
        conversation_id: str | None = None,
        allowed_permissions: set[ToolPermission] | None = None,
    ) -> str:
        if self.memory is not None and self.auto_remember:
            self.memory.remember_if_worthwhile(message)

        session_history = history
        conversation = None
        if conversation_id is not None:
            conversation = self.conversations.get_or_create(conversation_id)
            session_history = conversation.history()

        messages = self._build_messages(message, session_history)
        generate_turn = getattr(self.provider, "generate_turn", None)

        if generate_turn is None:
            response = self.provider.generate(messages)
            if conversation is not None:
                conversation.add(Message(role="user", content=message))
                conversation.add(Message(role="assistant", content=response))
            return response

        tool_specs = [
            {
                "name": spec.name,
                "description": spec.description,
                "permission": spec.permission.value,
                "input_schema": spec.input_schema,
            }
            for spec in self.tools.list_specs()
        ]

        for _ in range(self.max_tool_rounds):
            turn: ModelTurn = generate_turn(messages, tool_specs)
            if not turn.tool_calls:
                if conversation is not None:
                    conversation.add(Message(role="user", content=message))
                    conversation.add(Message(role="assistant", content=turn.text))
                return turn.text

            messages.append(
                Message(
                    role="assistant",
                    content=self._format_tool_calls(turn.tool_calls),
                )
            )

            for call in turn.tool_calls:
                result = self.execute_tool(
                    call.name,
                    call.arguments,
                    allowed_permissions=allowed_permissions,
                )
                messages.append(
                    Message(
                        role="tool",
                        content=self._format_tool_result(call, result),
                    )
                )

        if conversation is not None:
            conversation.add(Message(role="user", content=message))
            conversation.add(
                Message(
                    role="assistant",
                    content=(
                        "MARS stopped the tool loop after reaching its safety limit. "
                        "The requested task may require another step."
                    ),
                )
            )

        return (
            "MARS stopped the tool loop after reaching its safety limit. "
            "The requested task may require another step."
        )

    @staticmethod
    def _format_tool_calls(tool_calls: tuple[ToolCall, ...]) -> str:
        calls = [
            {"name": call.name, "arguments": call.arguments}
            for call in tool_calls
        ]
        return f"Tool calls requested: {calls}"

    @staticmethod
    def _format_tool_result(call: ToolCall, result: ToolResult) -> str:
        if result.success:
            return f"Tool result for {call.name}: {result.output!r}"
        return f"Tool error for {call.name}: {result.error}"

    def execute_tool(
        self,
        name: str,
        arguments: dict[str, object],
        *,
        allowed_permissions: set[ToolPermission] | None = None,
    ) -> ToolResult:
        """Execute a registered tool through the permission boundary."""
        return self.tools.execute(
            name,
            arguments,
            allowed_permissions=allowed_permissions,
        )
