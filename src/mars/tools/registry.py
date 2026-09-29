"""Tool registration, lookup, and permission enforcement."""

from .models import Tool, ToolPermission, ToolResult, ToolSpec


class ToolRegistry:
    """Central registry for authorized MARS capabilities."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        name = tool.spec.name.strip()
        if not name:
            raise ValueError("Tool name cannot be empty.")
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as error:
            raise KeyError(f"Unknown tool: {name}") from error

    def list_specs(self) -> list[ToolSpec]:
        return [tool.spec for tool in self._tools.values()]

    def execute(
        self,
        name: str,
        arguments: dict[str, object],
        *,
        allowed_permissions: set[ToolPermission] | None = None,
    ) -> ToolResult:
        tool = self.get(name)
        required = tool.spec.permission
        allowed = allowed_permissions or set()
        if required not in allowed:
            return ToolResult(
                success=False,
                error=f"Permission denied for tool '{name}': {required.value}",
            )
        return tool.execute(arguments)
