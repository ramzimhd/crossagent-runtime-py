"""Contracts describing tasks, agent state, and the per-session context."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crossagents.abstractions.audit import AuditEvent
    from crossagents.abstractions.memory import ActiveContext
    from crossagents.abstractions.models import ModelProfile


class AgentTaskType(IntEnum):
    """The kind of work a task represents.

    The selector uses this hint together with model capabilities and policy to
    decide which pattern to run.
    """

    GENERIC = 0
    QUESTION = 1
    PLAN = 2
    EXTRACT = 3
    VALIDATE = 4
    TRANSFORM = 5
    DECISION = 6


class AgentState(IntEnum):
    """Lifecycle state of an in-flight agent session."""

    PENDING = 0
    PLANNING = 1
    EXECUTING = 2
    VALIDATING = 3
    COMPLETED = 4
    FAILED = 5
    REJECTED = 6


@dataclass(frozen=True, kw_only=True)
class AgentTask:
    """The unit of work submitted to ``AgentRuntime``.

    Tasks are immutable so a single instance can be safely re-used across
    retries or sessions.
    """

    task_id: str
    input: str
    type: AgentTaskType = AgentTaskType.GENERIC
    requires_tools: bool = False
    requires_memory: bool = False
    requires_validation: bool = True
    max_steps: int | None = None
    allowed_pattern_ids: frozenset[str] | None = None
    forbidden_pattern_ids: frozenset[str] | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class AgentContext:
    """Read-only execution context handed to a pattern.

    Patterns receive a context per session and never share mutable state
    through it.
    """

    session_id: str
    task: AgentTask
    model: "ModelProfile"
    active_context: "ActiveContext | None" = None
    properties: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class AgentResult:
    """The outcome of executing a single pattern within a session."""

    session_id: str
    state: AgentState
    output: str = ""
    validation_passed: bool = False
    audit_events: tuple["AuditEvent", ...] = ()
    error_message: str | None = None
