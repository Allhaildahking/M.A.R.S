"""Tool contracts and execution results.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol


class ToolPermission(StrEnum):
    """Minimum authorization required to run a tool."""

    READ = "read"
    WRITE = "write"
    EXTERNAL_ACTION = "external_action"


@dataclass(frozen=True)
class ToolSpec:
    """Metadata and contract exposed to the reasoning layer."""

    name: str
    description: str
    permission: ToolPermission
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    """Normalized result returned by a tool."""

    success: bool
    output: Any = None
    error: str | None = None


class Tool(Protocol):
    """Protocol implemented by executable MARS tools."""

    @property
    def spec(self) -> ToolSpec:
        """Return this tool's public contract."""

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Execute the tool with validated arguments."""
