"""Application-supplied policy and the engine contract that evaluates it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from crossagents.abstractions.agents import AgentTask
    from crossagents.abstractions.models import ModelProfile
    from crossagents.abstractions.patterns import PatternDescriptor


@dataclass(frozen=True, kw_only=True)
class PolicyDecision:
    """Result of a policy evaluation.

    ``reason`` is required when ``allowed`` is false so audit logs and error
    messages can explain rejection.
    """

    allowed: bool
    reason: str | None = None

    @staticmethod
    def allow() -> "PolicyDecision":
        return PolicyDecision(allowed=True)

    @staticmethod
    def deny(reason: str) -> "PolicyDecision":
        return PolicyDecision(allowed=False, reason=reason)


@dataclass(frozen=True, kw_only=True)
class AgentPolicy:
    """Application-supplied constraints that apply to a session.

    Policies are declarative: the runtime evaluates them, the patterns consume
    the result.
    """

    allowed_patterns: frozenset[str] | None = None
    forbidden_patterns: frozenset[str] | None = None
    allowed_tools: frozenset[str] | None = None
    forbidden_tools: frozenset[str] | None = None
    max_steps: int = 8
    require_audit: bool = True
    require_validation: bool = True
    allow_memory: bool = True
    allow_tools: bool = True


class IPolicyEngine(Protocol):
    """Application-replaceable evaluator for policy rules.

    The runtime ships with a default implementation; advanced applications may
    substitute their own.
    """

    @property
    def policy(self) -> AgentPolicy: ...

    def evaluate_pattern_selection(
        self,
        task: "AgentTask",
        pattern: "PatternDescriptor",
        model: "ModelProfile",
    ) -> PolicyDecision: ...

    def evaluate_tool_call(self, task: "AgentTask", tool_name: str) -> PolicyDecision: ...
