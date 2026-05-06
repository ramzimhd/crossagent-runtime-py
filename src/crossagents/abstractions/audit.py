"""Audit event types and the sink protocol."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Protocol


class AuditEventKind(IntEnum):
    """Canonical audit event kinds emitted by the runtime, patterns, and tooling layer.

    New values may be added at the end; existing values must not be reused or
    reordered.
    """

    SESSION_STARTED = 0
    TASK_RECEIVED = 1
    MODEL_SELECTED = 2
    PATTERN_SELECTED = 3
    STEP_STARTED = 4
    STEP_COMPLETED = 5
    TOOL_CALL_REQUESTED = 6
    TOOL_CALL_APPROVED = 7
    TOOL_CALL_REJECTED = 8
    TOOL_RESULT_RECEIVED = 9
    VALIDATION_PASSED = 10
    VALIDATION_FAILED = 11
    SESSION_COMPLETED = 12
    SESSION_FAILED = 13
    POLICY_REJECTED = 14


@dataclass(frozen=True, kw_only=True)
class AuditEvent:
    """A single audit event.

    Events are immutable, deterministic, and free of model content payloads by
    design - sinks may attach additional context if needed.
    """

    timestamp: datetime
    session_id: str
    kind: AuditEventKind
    message: str = ""
    properties: Mapping[str, str] = field(default_factory=dict)


class IAuditSink(Protocol):
    """Destination for audit events.

    Implementations must be safe to call from multiple sessions concurrently.
    Sinks must not throw for ordinary write failures; degrade by dropping the
    event and surfacing diagnostics elsewhere.
    """

    async def write(self, event: AuditEvent) -> None: ...
