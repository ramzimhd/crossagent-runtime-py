"""Audit sink that retains every event in order. Useful for assertions."""

from __future__ import annotations

from crossagent.abstractions.audit import AuditEvent, IAuditSink


class InMemoryAuditSink(IAuditSink):
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    async def write(self, event: AuditEvent) -> None:
        self._events.append(event)
