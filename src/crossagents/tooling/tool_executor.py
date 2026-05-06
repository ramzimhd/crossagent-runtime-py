"""Runs a single, already-validated tool call against an ``ITool``."""

from __future__ import annotations

import asyncio

from crossagents.abstractions.tools import ITool, ToolCall, ToolResult


class ToolExecutor:
    """The executor catches and converts unexpected tool exceptions into a
    failed ``ToolResult``. Cancellation propagates.
    """

    async def execute(self, tool: ITool, call: ToolCall) -> ToolResult:
        if tool is None:
            raise ValueError("tool must not be None")
        if call is None:
            raise ValueError("call must not be None")

        try:
            return await tool.invoke(call)
        except asyncio.CancelledError:
            raise
        except Exception as ex:  # noqa: BLE001 - mirror .NET catch-all
            return ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=False,
                output="",
                error=f"{type(ex).__name__}: {ex}",
            )
