from __future__ import annotations

import pytest

from crossagent.core import AgentRuntime
from crossagent.patterns import NoToolPattern
from tests.fixtures import echo_adapter


def test_register_model_adds_model_to_registry() -> None:
    runtime = AgentRuntime()
    adapter = echo_adapter("model-a")

    runtime.register_model(adapter)

    assert "model-a" in runtime.models
    assert runtime.models["model-a"] is adapter


def test_register_model_rejects_duplicate_profile_id() -> None:
    runtime = AgentRuntime()
    runtime.register_model(echo_adapter("dup"))

    with pytest.raises(RuntimeError):
        runtime.register_model(echo_adapter("dup"))


def test_register_pattern_adds_pattern_to_registry() -> None:
    runtime = AgentRuntime()
    pattern = NoToolPattern()

    runtime.register_pattern(pattern)

    assert len(runtime.patterns) == 1
    assert runtime.patterns[0] is pattern
