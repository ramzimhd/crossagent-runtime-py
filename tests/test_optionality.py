from __future__ import annotations

from crossagent.abstractions.agents import AgentTask
from crossagent.core import AgentRuntime, RuntimeOptions, known_pattern_ids
from crossagent.memory import (
    ContextCompressor,
    MemoryRanker,
    MemoryRetriever,
    SlidingMemoryBuffer,
)
from crossagent.patterns import NoToolPattern
from crossagent.testing import FakeMemoryProvider, InMemoryAuditSink
from tests.fixtures import echo_adapter


async def test_runtime_runs_task_without_tooling() -> None:
    runtime = AgentRuntime(RuntimeOptions(audit_sink=InMemoryAuditSink()))
    runtime.register_model(echo_adapter()).register_pattern(NoToolPattern())

    task = AgentTask(task_id="no-tools", input="hello", requires_validation=False)
    result = await runtime.run(task, "echo")

    assert result.success
    assert runtime.tools is None
    assert result.selected_pattern_id == known_pattern_ids.NO_TOOL
    assert result.agent is not None
    assert result.agent.output == "hello"


async def test_runtime_runs_task_without_memory() -> None:
    runtime = AgentRuntime(RuntimeOptions(audit_sink=InMemoryAuditSink()))
    runtime.register_model(echo_adapter()).register_pattern(NoToolPattern())

    task = AgentTask(task_id="no-memory", input="ping", requires_validation=False)
    result = await runtime.run(task, "echo")

    assert result.success
    assert runtime.memory is None
    assert result.agent is not None
    assert result.agent.output == "ping"


def test_memory_layer_components_are_drop_in_replaceable() -> None:
    provider = FakeMemoryProvider()
    retriever = MemoryRetriever(provider)
    ranker = MemoryRanker()
    compressor = ContextCompressor(max_tokens=64)
    buffer: SlidingMemoryBuffer[str] = SlidingMemoryBuffer(capacity=4)

    assert retriever is not None
    assert ranker is not None
    assert compressor is not None
    assert buffer is not None
