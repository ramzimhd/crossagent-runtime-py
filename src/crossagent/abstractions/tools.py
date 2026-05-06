"""Tool definitions, calls, results, the per-tool contract, and the registry contract."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, kw_only=True)
class ToolDefinition:
    """Public description of a tool a model may invoke.

    The framework treats ``parameters_json_schema`` as opaque text; concrete
    tooling layers are responsible for validating arguments against it.
    """

    name: str
    description: str
    parameters_json_schema: str


@dataclass(frozen=True, kw_only=True)
class ToolCall:
    """A model's request to invoke a tool.

    ``arguments_json`` is the raw JSON produced by the model and is validated
    by the tooling layer before invocation.
    """

    call_id: str
    tool_name: str
    arguments_json: str


@dataclass(frozen=True, kw_only=True)
class ToolResult:
    """The outcome of a tool invocation.

    Tools must populate either ``output`` (on success) or ``error`` (on
    failure) and never both.
    """

    call_id: str
    tool_name: str
    success: bool = False
    output: str = ""
    error: str | None = None


@dataclass(frozen=True, kw_only=True)
class ToolPolicy:
    """Constraints applied to tool usage within a single session."""

    allowed_tools: frozenset[str] | None = None
    forbidden_tools: frozenset[str] | None = None
    max_calls_per_session: int = 16


class ITool(Protocol):
    """A single tool that can be exposed to a model.

    Implementations must be safe to invoke from multiple sessions concurrently
    and must not throw for ordinary tool failures - they should return a
    ``ToolResult`` with ``success=False`` instead.
    """

    @property
    def definition(self) -> ToolDefinition: ...

    async def invoke(self, call: ToolCall) -> ToolResult: ...


class IToolInvoker(Protocol):
    """Abstraction over the tooling layer used by the runtime and patterns.

    This keeps the core decoupled from any concrete ``ToolRegistry``
    implementation so applications can substitute their own.
    """

    def try_get(self, tool_name: str) -> ITool | None: ...

    def get_definitions(self) -> Sequence[ToolDefinition]: ...

    async def invoke(self, call: ToolCall) -> ToolResult: ...
