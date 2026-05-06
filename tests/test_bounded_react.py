from __future__ import annotations

import pytest

from crossagent.patterns import BoundedReActOptions, BoundedReActPattern


def test_unbounded_max_steps_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unbounded ReAct is rejected by design"):
        BoundedReActPattern(
            BoundedReActOptions(
                max_steps=0,
                allowed_tools=["noop"],
                step_timeout_seconds=5.0,
            )
        )


def test_empty_allowed_tools_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one tool"):
        BoundedReActPattern(
            BoundedReActOptions(
                max_steps=4,
                allowed_tools=[],
                step_timeout_seconds=5.0,
            )
        )


def test_negative_timeout_is_rejected() -> None:
    with pytest.raises(ValueError, match="step_timeout_seconds must be greater than zero"):
        BoundedReActPattern(
            BoundedReActOptions(
                max_steps=4,
                allowed_tools=["noop"],
                step_timeout_seconds=0.0,
            )
        )


def test_disabled_audit_is_rejected() -> None:
    with pytest.raises(ValueError, match="require_audit must be True"):
        BoundedReActPattern(
            BoundedReActOptions(
                max_steps=4,
                allowed_tools=["noop"],
                step_timeout_seconds=5.0,
                require_audit=False,
            )
        )


def test_bounded_configuration_succeeds() -> None:
    pattern = BoundedReActPattern(
        BoundedReActOptions(
            max_steps=3,
            allowed_tools=["echo"],
            step_timeout_seconds=2.0,
        )
    )
    assert pattern.descriptor.max_steps == 3
    assert pattern.descriptor.is_bounded is True
