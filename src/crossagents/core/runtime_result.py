"""Result of ``AgentRuntime.run``."""

from __future__ import annotations

from dataclasses import dataclass

from crossagents.abstractions.agents import AgentResult
from crossagents.abstractions.audit import AuditEvent
from crossagents.core.runtime_error import RuntimeErrorInfo


@dataclass(frozen=True, kw_only=True)
class RuntimeResult:
    """Contains either an ``AgentResult`` or a ``RuntimeErrorInfo``, never both."""

    session_id: str
    success: bool
    agent: AgentResult | None = None
    error: RuntimeErrorInfo | None = None
    runtime_audit_events: tuple[AuditEvent, ...] = ()
    selected_pattern_id: str | None = None
    selected_model_id: str | None = None
