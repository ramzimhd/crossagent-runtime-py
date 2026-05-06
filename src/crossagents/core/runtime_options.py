"""Configuration handed to ``AgentRuntime`` at construction time."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from crossagents.abstractions.audit import IAuditSink
from crossagents.abstractions.memory import IMemoryProvider
from crossagents.abstractions.policy import AgentPolicy
from crossagents.abstractions.tools import IToolInvoker


def _default_session_id() -> str:
    return uuid.uuid4().hex


def _default_timestamp() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class RuntimeOptions:
    """All services are optional except the audit sink; a ``NullAuditSink``
    is assigned when no sink is provided.
    """

    default_policy: AgentPolicy = field(default_factory=AgentPolicy)
    audit_sink: IAuditSink | None = None
    tools: IToolInvoker | None = None
    memory: IMemoryProvider | None = None
    preferred_pattern_id: str | None = None
    timestamp_factory: Callable[[], datetime] = _default_timestamp
    session_id_factory: Callable[[], str] = _default_session_id
