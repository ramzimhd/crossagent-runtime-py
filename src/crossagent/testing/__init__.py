"""Deterministic test doubles."""

from crossagent.testing.deterministic_clock import DeterministicClock
from crossagent.testing.fake_memory_provider import FakeMemoryProvider
from crossagent.testing.fake_model_adapter import FakeModelAdapter
from crossagent.testing.fake_tool import FakeTool
from crossagent.testing.in_memory_audit_sink import InMemoryAuditSink
from crossagent.testing.pattern_test_harness import PatternTestHarness

__all__ = [
    "DeterministicClock",
    "FakeMemoryProvider",
    "FakeModelAdapter",
    "FakeTool",
    "InMemoryAuditSink",
    "PatternTestHarness",
]
