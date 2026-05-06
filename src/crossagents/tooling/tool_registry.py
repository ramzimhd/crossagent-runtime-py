"""Default ``IToolInvoker`` implementation: name-based registry + normalizer + validator + executor."""

from __future__ import annotations

from collections.abc import Sequence

from crossagents.abstractions.tools import (
    ITool,
    IToolInvoker,
    ToolCall,
    ToolDefinition,
    ToolResult,
)
from crossagents.tooling.tool_call_normalizer import ToolCallNormalizer
from crossagents.tooling.tool_executor import ToolExecutor
from crossagents.tooling.tool_validator import ToolValidator


class ToolRegistry(IToolInvoker):
    """Looks up tools by name, normalises and validates calls, and dispatches
    to the registered ``ITool``. Registration is by name and is case-sensitive
    to match how providers report tool calls.
    """

    def __init__(
        self,
        validator: ToolValidator | None = None,
        executor: ToolExecutor | None = None,
        normalizer: ToolCallNormalizer | None = None,
    ) -> None:
        self._validator = validator if validator is not None else ToolValidator()
        self._executor = executor if executor is not None else ToolExecutor()
        self._normalizer = normalizer if normalizer is not None else ToolCallNormalizer()
        self._tools: dict[str, ITool] = {}

    @property
    def count(self) -> int:
        return len(self._tools)

    def register(self, tool: ITool) -> "ToolRegistry":
        if tool is None:
            raise ValueError("tool must not be None")
        if not tool.definition.name or not tool.definition.name.strip():
            raise ValueError("tool.definition.name must be non-empty.")
        if tool.definition.name in self._tools:
            raise RuntimeError(f"A tool named '{tool.definition.name}' is already registered.")
        self._tools[tool.definition.name] = tool
        return self

    def try_get(self, tool_name: str) -> ITool | None:
        if not tool_name or not tool_name.strip():
            return None
        return self._tools.get(tool_name)

    def get_definitions(self) -> Sequence[ToolDefinition]:
        return tuple(t.definition for t in self._tools.values())

    async def invoke(self, call: ToolCall) -> ToolResult:
        if call is None:
            raise ValueError("call must not be None")
        normalized = self._normalizer.normalize(call)

        tool = self._tools.get(normalized.tool_name)
        if tool is None:
            return ToolResult(
                call_id=normalized.call_id,
                tool_name=normalized.tool_name,
                success=False,
                error=f"Unknown tool '{normalized.tool_name}'.",
            )

        validation = self._validator.validate(tool.definition, normalized)
        if not validation.is_valid:
            return ToolResult(
                call_id=normalized.call_id,
                tool_name=normalized.tool_name,
                success=False,
                error=validation.reason or "Invalid arguments.",
            )

        return await self._executor.execute(tool, normalized)
