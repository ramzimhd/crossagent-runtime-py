from __future__ import annotations

from crossagents.abstractions.agents import AgentTask
from crossagents.core import AgentRuntime, RuntimeOptions
from crossagents.patterns import NoToolPattern
from crossagents.testing import InMemoryAuditSink
from tests.fixtures import echo_adapter


async def test_same_task_produces_identical_output_with_fake_adapter() -> None:
    runtime = AgentRuntime(RuntimeOptions(audit_sink=InMemoryAuditSink()))
    runtime.register_model(echo_adapter()).register_pattern(NoToolPattern())

    task = AgentTask(task_id="det", input="deterministic", requires_validation=False)
    first = await runtime.run(task, "echo")
    second = await runtime.run(task, "echo")

    assert first.success
    assert second.success
    assert first.agent is not None
    assert second.agent is not None
    assert first.agent.output == second.agent.output
