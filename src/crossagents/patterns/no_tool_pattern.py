"""Single model call with no tool use, no memory, and no validation phase."""

from __future__ import annotations

from datetime import datetime, timezone

from crossagents.abstractions.agents import AgentContext, AgentResult, AgentState
from crossagents.abstractions.audit import AuditEvent, AuditEventKind
from crossagents.abstractions.models import ModelRequest
from crossagents.abstractions.patterns import IAgentPattern, IPatternServices, PatternDescriptor, PatternRiskLevel
from crossagents.core import known_pattern_ids


class NoToolPattern(IAgentPattern):
    """The safest possible pattern; suitable for direct question answering or
    transformations that don't require external context.
    """

    _DESCRIPTOR = PatternDescriptor(
        pattern_id=known_pattern_ids.NO_TOOL,
        name="No-tool single call",
        is_bounded=True,
        max_steps=1,
        risk_level=PatternRiskLevel.LOW,
    )

    @property
    def descriptor(self) -> PatternDescriptor:
        return self._DESCRIPTOR

    async def execute(
        self,
        context: AgentContext,
        services: IPatternServices,
    ) -> AgentResult:
        if context is None:
            raise ValueError("context must not be None")
        if services is None:
            raise ValueError("services must not be None")

        await services.audit.write(
            AuditEvent(
                timestamp=datetime.now(timezone.utc),
                session_id=context.session_id,
                kind=AuditEventKind.STEP_STARTED,
                message="no-tool: single call",
            )
        )

        response = await services.model.complete(ModelRequest(prompt=context.task.input))

        await services.audit.write(
            AuditEvent(
                timestamp=datetime.now(timezone.utc),
                session_id=context.session_id,
                kind=AuditEventKind.STEP_COMPLETED,
                message="no-tool: single call completed",
            )
        )

        return AgentResult(
            session_id=context.session_id,
            state=AgentState.COMPLETED,
            output=response.content,
            validation_passed=True,
        )
