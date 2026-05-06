"""Lightweight harness for exercising a single pattern in isolation."""

from __future__ import annotations

import uuid

from crossagent.abstractions.agents import AgentContext, AgentResult, AgentTask
from crossagent.abstractions.memory import IMemoryProvider
from crossagent.abstractions.models import IModelAdapter
from crossagent.abstractions.patterns import IAgentPattern
from crossagent.abstractions.policy import AgentPolicy
from crossagent.abstractions.tools import IToolInvoker
from crossagent.core.pattern_services import PatternServices
from crossagent.core.runtime_policy_engine import RuntimePolicyEngine
from crossagent.testing.in_memory_audit_sink import InMemoryAuditSink


class PatternTestHarness:
    """Exercises a pattern without going through the full ``AgentRuntime`` path."""

    def __init__(self, model: IModelAdapter) -> None:
        if model is None:
            raise ValueError("model must not be None")
        self.model = model
        self.tools: IToolInvoker | None = None
        self.memory: IMemoryProvider | None = None
        self.audit = InMemoryAuditSink()
        self.policy: AgentPolicy = AgentPolicy()

    async def run(self, pattern: IAgentPattern, task: AgentTask) -> AgentResult:
        if pattern is None:
            raise ValueError("pattern must not be None")
        if task is None:
            raise ValueError("task must not be None")

        policy_engine = RuntimePolicyEngine(self.policy)
        session_id = uuid.uuid4().hex
        context = AgentContext(
            session_id=session_id,
            task=task,
            model=self.model.profile,
        )
        services = PatternServices(
            session_id=session_id,
            model=self.model,
            audit=self.audit,
            policy=policy_engine,
            effective_policy=self.policy,
            tools=self.tools,
            memory=self.memory,
        )
        return await pattern.execute(context, services)
