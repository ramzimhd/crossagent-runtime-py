"""The host that owns the registered models, patterns, services, and policy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Self

from crossagent.abstractions.agents import AgentState, AgentTask
from crossagent.abstractions.audit import AuditEventKind
from crossagent.abstractions.memory import IMemoryProvider
from crossagent.abstractions.models import IModelAdapter
from crossagent.abstractions.patterns import IAgentPattern, PatternDescriptor, PatternRiskLevel
from crossagent.abstractions.policy import AgentPolicy, IPolicyEngine
from crossagent.abstractions.tools import IToolInvoker
from crossagent.core.agent_session import AgentSession
from crossagent.core.audit_pipeline import AuditPipeline
from crossagent.core.null_audit_sink import NullAuditSink
from crossagent.core.pattern_selector import PatternSelector
from crossagent.core.runtime_error import RuntimeErrorCode, RuntimeErrorInfo
from crossagent.core.runtime_options import RuntimeOptions
from crossagent.core.runtime_policy_engine import RuntimePolicyEngine
from crossagent.core.runtime_result import RuntimeResult


class AgentRuntime:
    """Applications instantiate one runtime, register what they need, and call
    ``run_async`` per task.
    """

    def __init__(self, options: RuntimeOptions | None = None) -> None:
        self._options = options if options is not None else RuntimeOptions()
        if self._options.audit_sink is None:
            self._options.audit_sink = NullAuditSink.instance()
        self._models: dict[str, IModelAdapter] = {}
        self._patterns: list[IAgentPattern] = []
        self._policy = RuntimePolicyEngine(self._options.default_policy)
        self._selector = PatternSelector(self._policy)

    @property
    def policy(self) -> IPolicyEngine:
        return self._policy

    @property
    def tools(self) -> IToolInvoker | None:
        return self._options.tools

    @property
    def memory(self) -> IMemoryProvider | None:
        return self._options.memory

    @property
    def models(self) -> Mapping[str, IModelAdapter]:
        return self._models

    @property
    def patterns(self) -> tuple[IAgentPattern, ...]:
        return tuple(self._patterns)

    def register_model(self, adapter: IModelAdapter) -> Self:
        if adapter is None:
            raise ValueError("adapter must not be None")
        if not adapter.profile.profile_id or not adapter.profile.profile_id.strip():
            raise ValueError("ModelAdapter.profile.profile_id must be non-empty.")
        if adapter.profile.profile_id in self._models:
            raise RuntimeError(
                f"A model with id '{adapter.profile.profile_id}' is already registered."
            )
        self._models[adapter.profile.profile_id] = adapter
        return self

    def register_pattern(self, pattern: IAgentPattern) -> Self:
        if pattern is None:
            raise ValueError("pattern must not be None")
        self._validate_pattern_descriptor(pattern.descriptor)
        self._patterns.append(pattern)
        return self

    @staticmethod
    def _validate_pattern_descriptor(descriptor: PatternDescriptor) -> None:
        if descriptor is None:
            raise ValueError("descriptor must not be None")
        if not descriptor.pattern_id or not descriptor.pattern_id.strip():
            raise ValueError("PatternDescriptor.pattern_id must be non-empty.")
        if descriptor.risk_level == PatternRiskLevel.UNBOUNDED:
            raise ValueError(
                f"Unbounded patterns are not permitted. Pattern '{descriptor.pattern_id}' was registered with risk_level=UNBOUNDED."
            )
        if descriptor.is_bounded and descriptor.max_steps <= 0:
            raise ValueError(
                f"Bounded pattern '{descriptor.pattern_id}' must declare max_steps > 0."
            )

    @staticmethod
    def _property(key: str, value: str) -> Mapping[str, str]:
        return {key: value}

    async def run(
        self,
        task: AgentTask,
        model_profile_id: str,
        task_policy: AgentPolicy | None = None,
    ) -> RuntimeResult:
        if task is None:
            raise ValueError("task must not be None")
        if model_profile_id is None:
            raise ValueError("model_profile_id must not be None")

        session_id = self._options.session_id_factory()
        sink = self._options.audit_sink
        assert sink is not None
        pipeline = AuditPipeline(sink, self._options.timestamp_factory, session_id)

        await pipeline.emit(
            AuditEventKind.SESSION_STARTED,
            "Session started.",
            self._property("sessionId", session_id),
        )
        await pipeline.emit(
            AuditEventKind.TASK_RECEIVED,
            f"Task '{task.task_id}' of type '{task.type.name.lower()}'.",
            self._property("taskId", task.task_id),
        )

        model = self._models.get(model_profile_id)
        if model is None:
            return await self._fail(
                pipeline,
                session_id,
                RuntimeErrorCode.UNKNOWN_MODEL,
                f"No model is registered with profile id '{model_profile_id}'.",
            )

        await pipeline.emit(
            AuditEventKind.MODEL_SELECTED,
            f"Model '{model.profile.profile_id}' selected.",
            self._property("modelId", model.profile.profile_id),
        )

        effective_policy = task_policy if task_policy is not None else self._options.default_policy
        if effective_policy is self._options.default_policy:
            policy_engine: IPolicyEngine = self._policy
            selector = self._selector
        else:
            policy_engine = RuntimePolicyEngine(effective_policy)
            selector = PatternSelector(policy_engine)

        selection = selector.select(
            task,
            model.profile,
            self._patterns,
            self._options.preferred_pattern_id,
        )
        selected_pattern = selection.pattern
        if not selection.has_selection or selected_pattern is None:
            await pipeline.emit(
                AuditEventKind.POLICY_REJECTED,
                f"No pattern selected. {selection.reason}",
            )
            return RuntimeResult(
                session_id=session_id,
                success=False,
                error=RuntimeErrorInfo(
                    code=RuntimeErrorCode.NO_ELIGIBLE_PATTERN,
                    message="No eligible pattern.",
                    detail=selection.reason,
                ),
                runtime_audit_events=pipeline.captured,
                selected_model_id=model.profile.profile_id,
            )

        await pipeline.emit(
            AuditEventKind.PATTERN_SELECTED,
            f"Pattern '{selected_pattern.descriptor.pattern_id}' selected.",
            self._property("patternId", selected_pattern.descriptor.pattern_id),
        )

        session = AgentSession(
            self,
            session_id,
            task,
            model,
            selected_pattern,
            policy_engine,
            effective_policy,
            pipeline,
        )
        agent_result = await session.run()

        success = agent_result.state == AgentState.COMPLETED
        await pipeline.emit(
            AuditEventKind.SESSION_COMPLETED if success else AuditEventKind.SESSION_FAILED,
            "Session completed."
            if success
            else f"Session failed: {agent_result.error_message or 'unknown error'}.",
            self._property("sessionId", session_id),
        )

        return RuntimeResult(
            session_id=session_id,
            success=success,
            agent=agent_result,
            error=None
            if success
            else RuntimeErrorInfo(
                code=RuntimeErrorCode.EXECUTION_FAILED,
                message=agent_result.error_message or "Pattern reported a non-completed state.",
                detail=agent_result.state.name,
            ),
            runtime_audit_events=pipeline.captured,
            selected_pattern_id=selected_pattern.descriptor.pattern_id,
            selected_model_id=model.profile.profile_id,
        )

    async def _fail(
        self,
        pipeline: AuditPipeline,
        session_id: str,
        code: RuntimeErrorCode,
        message: str,
    ) -> RuntimeResult:
        await pipeline.emit(AuditEventKind.SESSION_FAILED, message)
        return RuntimeResult(
            session_id=session_id,
            success=False,
            error=RuntimeErrorInfo(code=code, message=message),
            runtime_audit_events=pipeline.captured,
        )
