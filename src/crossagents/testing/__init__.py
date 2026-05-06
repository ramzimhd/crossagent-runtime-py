"""Deterministic test doubles."""

from crossagents.testing.deterministic_clock import DeterministicClock
from crossagents.testing.fake_memory_provider import FakeMemoryProvider
from crossagents.testing.fake_model_adapter import FakeModelAdapter
from crossagents.testing.fake_tool import FakeTool
from crossagents.testing.in_memory_audit_sink import InMemoryAuditSink
from crossagents.testing.pattern_test_harness import PatternTestHarness

__all__ = [
    "DeterministicClock",
    "FakeMemoryProvider",
    "FakeModelAdapter",
    "FakeTool",
    "InMemoryAuditSink",
    "PatternTestHarness",
]
