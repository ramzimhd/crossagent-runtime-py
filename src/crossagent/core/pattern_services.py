"""Concrete ``IPatternServices`` honoring the effective policy gates."""

from __future__ import annotations

from crossagent.abstractions.audit import IAuditSink
from crossagent.abstractions.memory import IMemoryProvider
from crossagent.abstractions.models import IModelAdapter
from crossagent.abstractions.patterns import IPatternServices
from crossagent.abstractions.policy import AgentPolicy, IPolicyEngine
from crossagent.abstractions.tools import IToolInvoker


class PatternServices(IPatternServices):
    """Memory and tools surface as ``None`` when the policy disables them, even
    if the runtime was configured with concrete instances.
    """

    def __init__(
        self,
        session_id: str,
        model: IModelAdapter,
        audit: IAuditSink,
        policy: IPolicyEngine,
        effective_policy: AgentPolicy,
        tools: IToolInvoker | None,
        memory: IMemoryProvider | None,
    ) -> None:
        if not session_id:
            raise ValueError("session_id must not be empty")
        if model is None:
            raise ValueError("model must not be None")
        if audit is None:
            raise ValueError("audit must not be None")
        if policy is None:
            raise ValueError("policy must not be None")
        if effective_policy is None:
            raise ValueError("effective_policy must not be None")

        self._session_id = session_id
        self._model = model
        self._audit = audit
        self._policy = policy
        self._effective_policy = effective_policy
        self._tools = tools if effective_policy.allow_tools else None
        self._memory = memory if effective_policy.allow_memory else None

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def model(self) -> IModelAdapter:
        return self._model

    @property
    def tools(self) -> IToolInvoker | None:
        return self._tools

    @property
    def memory(self) -> IMemoryProvider | None:
        return self._memory

    @property
    def audit(self) -> IAuditSink:
        return self._audit

    @property
    def policy(self) -> IPolicyEngine:
        return self._policy

    @property
    def effective_policy(self) -> AgentPolicy:
        return self._effective_policy
