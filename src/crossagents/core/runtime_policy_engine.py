"""Default ``IPolicyEngine`` implementation."""

from __future__ import annotations

from crossagents.abstractions.agents import AgentTask, AgentTaskType
from crossagents.abstractions.models import ModelProfile
from crossagents.abstractions.patterns import PatternDescriptor, PatternRiskLevel
from crossagents.abstractions.policy import AgentPolicy, IPolicyEngine, PolicyDecision
from crossagents.core import known_pattern_ids


class RuntimePolicyEngine(IPolicyEngine):
    """Combines runtime defaults, the active task's allow/forbid lists, and
    capability gates to produce a single decision.
    """

    def __init__(self, policy: AgentPolicy) -> None:
        if policy is None:
            raise ValueError("policy must not be None")
        if policy.max_steps <= 0:
            raise ValueError("AgentPolicy.max_steps must be greater than zero.")
        self._policy = policy

    @property
    def policy(self) -> AgentPolicy:
        return self._policy

    def evaluate_pattern_selection(
        self,
        task: AgentTask,
        pattern: PatternDescriptor,
        model: ModelProfile,
    ) -> PolicyDecision:
        if task is None:
            raise ValueError("task must not be None")
        if pattern is None:
            raise ValueError("pattern must not be None")
        if model is None:
            raise ValueError("model must not be None")

        if pattern.risk_level == PatternRiskLevel.UNBOUNDED:
            return PolicyDecision.deny(
                f"Pattern '{pattern.pattern_id}' is unbounded; rejected by runtime."
            )

        if pattern.is_bounded and pattern.max_steps <= 0:
            return PolicyDecision.deny(
                f"Pattern '{pattern.pattern_id}' is marked bounded but has no max_steps."
            )

        allowed = self._policy.allowed_patterns
        if allowed and pattern.pattern_id not in allowed:
            return PolicyDecision.deny(
                f"Pattern '{pattern.pattern_id}' is not in the allowed pattern list."
            )

        forbidden = self._policy.forbidden_patterns
        if forbidden and pattern.pattern_id in forbidden:
            return PolicyDecision.deny(
                f"Pattern '{pattern.pattern_id}' is forbidden by policy."
            )

        task_allowed = task.allowed_pattern_ids
        if task_allowed and pattern.pattern_id not in task_allowed:
            return PolicyDecision.deny(
                f"Pattern '{pattern.pattern_id}' is not in the task's allowed pattern list."
            )

        task_forbidden = task.forbidden_pattern_ids
        if task_forbidden and pattern.pattern_id in task_forbidden:
            return PolicyDecision.deny(
                f"Pattern '{pattern.pattern_id}' is forbidden by the task."
            )

        if pattern.requires_tools and not self._policy.allow_tools:
            return PolicyDecision.deny(
                f"Pattern '{pattern.pattern_id}' requires tools but policy disables tools."
            )

        if pattern.requires_memory and not self._policy.allow_memory:
            return PolicyDecision.deny(
                f"Pattern '{pattern.pattern_id}' requires memory but policy disables memory."
            )

        if pattern.requires_native_tool_calling and not model.capabilities.supports_native_tool_calling:
            return PolicyDecision.deny(
                f"Model '{model.profile_id}' does not support native tool calling required by '{pattern.pattern_id}'."
            )

        if pattern.requires_json_mode and not (
            model.capabilities.supports_json_mode or model.capabilities.supports_json_schema
        ):
            return PolicyDecision.deny(
                f"Model '{model.profile_id}' does not support JSON mode required by '{pattern.pattern_id}'."
            )

        if (
            self._policy.require_validation
            and task.requires_validation
            and pattern.pattern_id == known_pattern_ids.NO_TOOL
            and task.type == AgentTaskType.VALIDATE
        ):
            return PolicyDecision.deny(
                f"Task '{task.task_id}' requires validation but pattern '{pattern.pattern_id}' does not provide a validation phase."
            )

        if task.max_steps is not None and pattern.is_bounded and pattern.max_steps > task.max_steps:
            return PolicyDecision.deny(
                f"Pattern '{pattern.pattern_id}' max_steps ({pattern.max_steps}) exceeds task max_steps ({task.max_steps})."
            )

        if pattern.is_bounded and pattern.max_steps > self._policy.max_steps:
            return PolicyDecision.deny(
                f"Pattern '{pattern.pattern_id}' max_steps ({pattern.max_steps}) exceeds policy max_steps ({self._policy.max_steps})."
            )

        return PolicyDecision.allow()

    def evaluate_tool_call(self, task: AgentTask, tool_name: str) -> PolicyDecision:
        if task is None:
            raise ValueError("task must not be None")
        if not tool_name or not tool_name.strip():
            return PolicyDecision.deny("Tool name was empty.")

        if not self._policy.allow_tools:
            return PolicyDecision.deny("Tool calling is disabled by policy.")

        allowed = self._policy.allowed_tools
        if allowed and tool_name not in allowed:
            return PolicyDecision.deny(f"Tool '{tool_name}' is not in the allowed tool list.")

        forbidden = self._policy.forbidden_tools
        if forbidden and tool_name in forbidden:
            return PolicyDecision.deny(f"Tool '{tool_name}' is forbidden by policy.")

        return PolicyDecision.allow()
