"""Configuration for ``BoundedReActPattern``."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class BoundedReActOptions:
    """The pattern intentionally has no no-argument constructor: every safety
    bound (max steps, allowed tools, timeout, audit requirement) must be
    supplied. Misconfigured options are rejected by the pattern's constructor
    so unbounded ReAct is impossible to instantiate.
    """

    max_steps: int
    allowed_tools: Sequence[str]
    step_timeout_seconds: float
    require_audit: bool = True
    stop_when_model_emits_no_tool_calls: bool = True

    def validate(self) -> None:
        if self.max_steps <= 0:
            raise ValueError(
                "BoundedReActOptions.max_steps must be greater than zero. "
                "Unbounded ReAct is rejected by design."
            )
        if not self.allowed_tools or len(self.allowed_tools) == 0:
            raise ValueError(
                "BoundedReActOptions.allowed_tools must contain at least one tool. "
                "Unbounded ReAct is rejected by design."
            )
        if self.step_timeout_seconds <= 0:
            raise ValueError(
                "BoundedReActOptions.step_timeout_seconds must be greater than zero."
            )
        if not self.require_audit:
            raise ValueError(
                "BoundedReActOptions.require_audit must be True; bounded ReAct execution requires audit logging."
            )
