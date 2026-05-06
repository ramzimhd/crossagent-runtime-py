"""Per-session audit pipeline that buffers events and fans them out to a sink."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import cast

from crossagent.abstractions.audit import AuditEvent, AuditEventKind, IAuditSink


class AuditPipeline:
    """Buffers audit events for one session and fans them out to a sink.

    The pipeline is single-session and single-threaded by design; sessions get
    their own pipeline instance.
    """

    def __init__(
        self,
        sink: IAuditSink,
        timestamp_factory: Callable[[], datetime],
        session_id: str,
    ) -> None:
        if sink is None:
            raise ValueError("sink must not be None")
        if timestamp_factory is None:
            raise ValueError("timestamp_factory must not be None")
        if not session_id:
            raise ValueError("session_id must not be empty")
        self._sink = sink
        self._time = timestamp_factory
        self._session_id = session_id
        self._captured: list[AuditEvent] = []

    @property
    def captured(self) -> tuple[AuditEvent, ...]:
        return tuple(self._captured)

    async def emit(
        self,
        kind: AuditEventKind,
        message: str,
        properties: Mapping[str, str] | None = None,
    ) -> None:
        event = AuditEvent(
            timestamp=self._time(),
            session_id=self._session_id,
            kind=kind,
            message=message,
            properties=dict(properties) if properties else {},
        )
        self._captured.append(event)
        await self._sink.write(event)

    def as_sink(self) -> IAuditSink:
        """Returns a sink that re-stamps events through this pipeline."""

        return cast(IAuditSink, _PipelineSink(self))


class _PipelineSink(IAuditSink):
    def __init__(self, pipeline: AuditPipeline) -> None:
        self._pipeline = pipeline

    async def write(self, event: AuditEvent) -> None:
        if event is None:
            raise ValueError("event must not be None")
        await self._pipeline.emit(event.kind, event.message, event.properties)
