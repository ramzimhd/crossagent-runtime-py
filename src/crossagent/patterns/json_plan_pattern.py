"""Skeleton pattern that asks the model for a JSON-encoded plan."""

from __future__ import annotations

from datetime import datetime, timezone

from crossagent.abstractions.agents import AgentContext, AgentResult, AgentState
from crossagent.abstractions.audit import AuditEvent, AuditEventKind
from crossagent.abstractions.models import ModelRequest
from crossagent.abstractions.patterns import IAgentPattern, IPatternServices, PatternDescriptor, PatternRiskLevel
from crossagent.core import known_pattern_ids


class JsonPlanPattern(IAgentPattern):
    """Requires the model to advertise JSON mode or JSON Schema support.

    The skeleton does not itself parse or validate the plan; consumers may
    layer schema validation on top via a custom pattern or a follow-up step.
    """

    _DESCRIPTOR = PatternDescriptor(
        pattern_id=known_pattern_ids.JSON_PLAN,
        name="JSON plan",
        requires_json_mode=True,
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
                message="json-plan: requesting structured plan",
            )
        )

        response = await services.model.complete(
            ModelRequest(
                prompt=(
                    "Produce a JSON object with a 'steps' array describing how to address the task. "
                    f"Do not include any prose.\n\nTask:\n{context.task.input}"
                ),
                json_mode=True,
            )
        )

        await services.audit.write(
            AuditEvent(
                timestamp=datetime.now(timezone.utc),
                session_id=context.session_id,
                kind=AuditEventKind.STEP_COMPLETED,
                message="json-plan: response received",
            )
        )

        return AgentResult(
            session_id=context.session_id,
            state=AgentState.COMPLETED,
            output=response.content,
            validation_passed=True,
        )
