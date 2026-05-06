from __future__ import annotations

from crossagent.abstractions.agents import AgentTask
from crossagent.abstractions.audit import AuditEventKind
from crossagent.core import AgentRuntime, RuntimeOptions
from crossagent.patterns import NoToolPattern
from crossagent.testing import InMemoryAuditSink
from tests.fixtures import echo_adapter


async def test_runtime_emits_canonical_audit_events() -> None:
    sink = InMemoryAuditSink()
    runtime = AgentRuntime(RuntimeOptions(audit_sink=sink))
    runtime.register_model(echo_adapter()).register_pattern(NoToolPattern())

    task = AgentTask(task_id="audit", input="hi", requires_validation=False)
    result = await runtime.run(task, "echo")

    assert result.success

    kinds = [e.kind for e in sink.events]
    assert AuditEventKind.SESSION_STARTED in kinds
    assert AuditEventKind.TASK_RECEIVED in kinds
    assert AuditEventKind.MODEL_SELECTED in kinds
    assert AuditEventKind.PATTERN_SELECTED in kinds
    assert AuditEventKind.SESSION_COMPLETED in kinds

    assert len(result.runtime_audit_events) > 0
    for evt in result.runtime_audit_events:
        assert evt.session_id == result.session_id
