"""Three-phase pattern: plan, execute, validate."""

from __future__ import annotations

from datetime import datetime, timezone

from crossagent.abstractions.agents import AgentContext, AgentResult, AgentState
from crossagent.abstractions.audit import AuditEvent, AuditEventKind
from crossagent.abstractions.models import ModelRequest, ModelResponse
from crossagent.abstractions.patterns import IAgentPattern, IPatternServices, PatternDescriptor, PatternRiskLevel
from crossagent.core import known_pattern_ids
from crossagent.core.execution_graph import ExecutionGraph


class PlanExecuteValidatePattern(IAgentPattern):
    """Phases are explicit and audited so applications can reason about what
    happened in each session.
    """

    _DESCRIPTOR = PatternDescriptor(
        pattern_id=known_pattern_ids.PLAN_EXECUTE_VALIDATE,
        name="Plan-Execute-Validate",
        is_bounded=True,
        max_steps=3,
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

        graph = ExecutionGraph().add_step("plan").add_step("execute").add_step("validate")

        plan_response = await self._run_step(
            services,
            context,
            graph.steps[0],
            f"Produce a short, ordered plan for the following task. Do not solve it yet.\n\nTask:\n{context.task.input}",
        )
        execute_response = await self._run_step(
            services,
            context,
            graph.steps[1],
            f"Plan:\n{plan_response.content}\n\nUsing the plan above, produce the final answer.\n\nTask:\n{context.task.input}",
        )
        validate_response = await self._run_step(
            services,
            context,
            graph.steps[2],
            f"Review the answer below for completeness against the task. Reply with the single word 'PASS' or 'FAIL' followed by a one-line reason.\n\nTask:\n{context.task.input}\n\nAnswer:\n{execute_response.content}",
        )

        validation_passed = validate_response.content.lstrip().upper().startswith("PASS")

        await services.audit.write(
            AuditEvent(
                timestamp=datetime.now(timezone.utc),
                session_id=context.session_id,
                kind=AuditEventKind.VALIDATION_PASSED if validation_passed else AuditEventKind.VALIDATION_FAILED,
                message=validate_response.content,
            )
        )

        return AgentResult(
            session_id=context.session_id,
            state=AgentState.COMPLETED,
            output=execute_response.content,
            validation_passed=validation_passed,
        )

    @staticmethod
    async def _run_step(
        services: IPatternServices,
        context: AgentContext,
        step_name: str,
        prompt: str,
    ) -> ModelResponse:
        await services.audit.write(
            AuditEvent(
                timestamp=datetime.now(timezone.utc),
                session_id=context.session_id,
                kind=AuditEventKind.STEP_STARTED,
                message=f"plan-execute-validate: {step_name} started",
            )
        )
        response = await services.model.complete(ModelRequest(prompt=prompt))
        await services.audit.write(
            AuditEvent(
                timestamp=datetime.now(timezone.utc),
                session_id=context.session_id,
                kind=AuditEventKind.STEP_COMPLETED,
                message=f"plan-execute-validate: {step_name} completed",
            )
        )
        return response
