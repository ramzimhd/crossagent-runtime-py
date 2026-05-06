"""Test tool that echoes its arguments by default."""

from __future__ import annotations

from collections.abc import Callable

from crossagents.abstractions.tools import ITool, ToolCall, ToolDefinition, ToolResult


Handler = Callable[[ToolCall], ToolResult]


class FakeTool(ITool):
    """Tests can supply a custom handler to return any payload or simulate failure."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters_json_schema: str,
        handler: Handler | None = None,
    ) -> None:
        self._definition = ToolDefinition(
            name=name,
            description=description,
            parameters_json_schema=parameters_json_schema,
        )
        self._handler = handler if handler is not None else self._default_handler

    @property
    def definition(self) -> ToolDefinition:
        return self._definition

    async def invoke(self, call: ToolCall) -> ToolResult:
        if call is None:
            raise ValueError("call must not be None")
        return self._handler(call)

    @staticmethod
    def _default_handler(call: ToolCall) -> ToolResult:
        return ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            success=True,
            output=call.arguments_json,
        )
