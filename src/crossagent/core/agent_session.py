"""One execution of one task."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from crossagent.abstractions.agents import AgentContext, AgentResult, AgentState, AgentTask
from crossagent.abstractions.models import IModelAdapter
from crossagent.abstractions.patterns import IAgentPattern
from crossagent.abstractions.policy import AgentPolicy, IPolicyEngine
from crossagent.core.audit_pipeline import AuditPipeline
from crossagent.core.pattern_services import PatternServices

if TYPE_CHECKING:
    from crossagent.core.agent_runtime import AgentRuntime


class AgentSession:
    """Sessions are short-lived: created, run, returned to the runtime, then
    discarded. They are not thread-safe and are not reused.
    """

    def __init__(
        self,
        owner: "AgentRuntime",
        session_id: str,
        task: AgentTask,
        model: IModelAdapter,
        pattern: IAgentPattern,
        policy: IPolicyEngine,
        effective_policy: AgentPolicy,
        audit: AuditPipeline,
    ) -> None:
        self._owner = owner
        self._session_id = session_id
        self._task = task
        self._model = model
        self._pattern = pattern
        self._policy = policy
        self._effective_policy = effective_policy
        self._audit = audit

    @property
    def session_id(self) -> str:
        return self._session_id

    async def run(self) -> AgentResult:
        context = AgentContext(
            session_id=self._session_id,
            task=self._task,
            model=self._model.profile,
            active_context=None,
        )
        services = PatternServices(
            session_id=self._session_id,
            model=self._model,
            audit=self._audit.as_sink(),
            policy=self._policy,
            effective_policy=self._effective_policy,
            tools=self._owner.tools,
            memory=self._owner.memory,
        )
        try:
            return await self._pattern.execute(context, services)
        except asyncio.CancelledError:
            return AgentResult(
                session_id=self._session_id,
                state=AgentState.FAILED,
                validation_passed=False,
                error_message="Cancelled.",
            )
        except Exception as exc:  # noqa: BLE001 - mirror .NET catch-all in session boundary
            return AgentResult(
                session_id=self._session_id,
                state=AgentState.FAILED,
                validation_passed=False,
                error_message=f"{type(exc).__name__}: {exc}",
            )
