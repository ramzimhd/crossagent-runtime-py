"""An audit sink that discards events. Useful for tests and policy-disabled audit."""

from __future__ import annotations

from crossagents.abstractions.audit import AuditEvent, IAuditSink


class NullAuditSink(IAuditSink):
    """A no-op audit sink. Use ``NullAuditSink.instance()`` to share the singleton."""

    _instance: "NullAuditSink | None" = None

    async def write(self, event: AuditEvent) -> None:  # noqa: ARG002
        return None

    @classmethod
    def instance(cls) -> "NullAuditSink":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
