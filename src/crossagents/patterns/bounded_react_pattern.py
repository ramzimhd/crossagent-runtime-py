"""A bounded reason-and-act loop."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from crossagents.abstractions.agents import AgentContext, AgentResult, AgentState
from crossagents.abstractions.audit import AuditEvent, AuditEventKind
from crossagents.abstractions.models import ModelRequest
from crossagents.abstractions.patterns import IAgentPattern, IPatternServices, PatternDescriptor, PatternRiskLevel
from crossagents.core import known_pattern_ids
from crossagents.patterns.bounded_react_options import BoundedReActOptions


class BoundedReActPattern(IAgentPattern):
    """Every loop iteration is a single model call optionally followed by a
    tool call; the loop terminates when the model stops requesting tools or
    when the configured step bound is hit. Unbounded ReAct configurations are
    rejected by ``BoundedReActOptions.validate``.
    """

    def __init__(self, options: BoundedReActOptions) -> None:
        if options is None:
            raise ValueError("options must not be None")
        options.validate()
        self._options = options
        self._allowed_tools = frozenset(options.allowed_tools)
        self._descriptor = PatternDescriptor(
            pattern_id=known_pattern_ids.BOUNDED_REACT,
            name="Bounded ReAct",
            requires_tools=True,
            requires_native_tool_calling=True,
            is_bounded=True,
            max_steps=options.max_steps,
            risk_level=PatternRiskLevel.MEDIUM,
        )

    @property
    def descriptor(self) -> PatternDescriptor:
        return self._descriptor

    async def execute(
        self,
        context: AgentContext,
        services: IPatternServices,
    ) -> AgentResult:
        if context is None:
            raise ValueError("context must not be None")
        if services is None:
            raise ValueError("services must not be None")

        if services.tools is None:
            return AgentResult(
                session_id=context.session_id,
                state=AgentState.REJECTED,
                error_message="BoundedReActPattern requires a tool invoker.",
            )

        tool_definitions = tuple(
            d for d in services.tools.get_definitions() if d.name in self._allowed_tools
        )
        if not tool_definitions:
            return AgentResult(
                session_id=context.session_id,
                state=AgentState.REJECTED,
                error_message="None of the allowed tools are registered.",
            )

        transcript = context.task.input
        last_response = None

        for step in range(1, self._options.max_steps + 1):
            await services.audit.write(
                AuditEvent(
                    timestamp=datetime.now(timezone.utc),
                    session_id=context.session_id,
                    kind=AuditEventKind.STEP_STARTED,
                    message=f"react: step {step} of {self._options.max_steps}",
                )
            )

            request = ModelRequest(prompt=transcript, tools=tool_definitions)
            try:
                response = await asyncio.wait_for(
                    services.model.complete(request),
                    timeout=self._options.step_timeout_seconds,
                )
            except asyncio.TimeoutError:
                return AgentResult(
                    session_id=context.session_id,
                    state=AgentState.FAILED,
                    output=last_response.content if last_response is not None else "",
                    error_message=(
                        f"Step {step} exceeded the configured timeout of "
                        f"{self._options.step_timeout_seconds}s."
                    ),
                )

            last_response = response

            if not response.tool_calls:
                await services.audit.write(
                    AuditEvent(
                        timestamp=datetime.now(timezone.utc),
                        session_id=context.session_id,
                        kind=AuditEventKind.STEP_COMPLETED,
                        message=f"react: step {step} produced final answer",
                    )
                )
                return AgentResult(
                    session_id=context.session_id,
                    state=AgentState.COMPLETED,
                    output=response.content,
                    validation_passed=True,
                )

            for tool_call in response.tool_calls:
                if tool_call.tool_name not in self._allowed_tools:
                    await services.audit.write(
                        AuditEvent(
                            timestamp=datetime.now(timezone.utc),
                            session_id=context.session_id,
                            kind=AuditEventKind.TOOL_CALL_REJECTED,
                            message=f"react: tool '{tool_call.tool_name}' is not allowed in this session",
                        )
                    )
                    continue

                decision = services.policy.evaluate_tool_call(context.task, tool_call.tool_name)
                if not decision.allowed:
                    await services.audit.write(
                        AuditEvent(
                            timestamp=datetime.now(timezone.utc),
                            session_id=context.session_id,
                            kind=AuditEventKind.TOOL_CALL_REJECTED,
                            message=decision.reason or "Tool call rejected by policy.",
                        )
                    )
                    continue

                await services.audit.write(
                    AuditEvent(
                        timestamp=datetime.now(timezone.utc),
                        session_id=context.session_id,
                        kind=AuditEventKind.TOOL_CALL_APPROVED,
                        message=f"react: invoking tool '{tool_call.tool_name}'",
                    )
                )

                tool_result = await services.tools.invoke(tool_call)

                await services.audit.write(
                    AuditEvent(
                        timestamp=datetime.now(timezone.utc),
                        session_id=context.session_id,
                        kind=AuditEventKind.TOOL_RESULT_RECEIVED,
                        message=f"react: tool '{tool_call.tool_name}' returned (success={tool_result.success})",
                    )
                )

                fragment = (
                    tool_result.output
                    if tool_result.success
                    else f"error: {tool_result.error}"
                )
                transcript = f"{transcript}\n[tool {tool_call.tool_name}] {fragment}"

            await services.audit.write(
                AuditEvent(
                    timestamp=datetime.now(timezone.utc),
                    session_id=context.session_id,
                    kind=AuditEventKind.STEP_COMPLETED,
                    message=f"react: step {step} completed",
                )
            )

        return AgentResult(
            session_id=context.session_id,
            state=AgentState.FAILED,
            output=last_response.content if last_response is not None else "",
            error_message=(
                f"Bounded ReAct exhausted {self._options.max_steps} step(s) without a final answer."
            ),
        )
