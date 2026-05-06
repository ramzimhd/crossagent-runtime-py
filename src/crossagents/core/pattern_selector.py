"""Deterministic selector that picks an ``IAgentPattern`` for a (task, model, policy) triple."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from crossagents.abstractions.agents import AgentTask, AgentTaskType
from crossagents.abstractions.models import ModelProfile
from crossagents.abstractions.patterns import (
    IAgentPattern,
    PatternDescriptor,
    PatternRequirement,
    PatternRiskLevel,
)
from crossagents.abstractions.policy import IPolicyEngine
from crossagents.core import known_pattern_ids


@dataclass(frozen=True, kw_only=True)
class PatternSelectionResult:
    """Outcome of ``PatternSelector.select``."""

    has_selection: bool
    pattern: IAgentPattern | None = None
    requirement: PatternRequirement | None = None
    rejections: tuple[str, ...] = ()
    reason: str | None = None

    @staticmethod
    def selected(
        pattern: IAgentPattern,
        requirement: PatternRequirement,
        rejections: Sequence[str],
    ) -> "PatternSelectionResult":
        return PatternSelectionResult(
            has_selection=True,
            pattern=pattern,
            requirement=requirement,
            rejections=tuple(rejections),
        )

    @staticmethod
    def none(reason: str) -> "PatternSelectionResult":
        return PatternSelectionResult(has_selection=False, reason=reason)


class PatternSelector:
    """Deterministic: given identical inputs and registration order it always
    returns the same result.
    """

    def __init__(self, policy: IPolicyEngine) -> None:
        if policy is None:
            raise ValueError("policy must not be None")
        self._policy = policy

    @staticmethod
    def derive_requirements(task: AgentTask, model: ModelProfile) -> PatternRequirement:
        if task is None:
            raise ValueError("task must not be None")
        if model is None:
            raise ValueError("model must not be None")
        return PatternRequirement(
            needs_tools=task.requires_tools,
            needs_memory=task.requires_memory,
            needs_validation=task.requires_validation,
            needs_json_mode=task.type
            in (AgentTaskType.PLAN, AgentTaskType.EXTRACT, AgentTaskType.DECISION),
            needs_multi_agent=False,
        )

    def select(
        self,
        task: AgentTask,
        model: ModelProfile,
        patterns: Sequence[IAgentPattern],
        preferred_pattern_id: str | None = None,
    ) -> PatternSelectionResult:
        if task is None:
            raise ValueError("task must not be None")
        if model is None:
            raise ValueError("model must not be None")
        if patterns is None:
            raise ValueError("patterns must not be None")
        if len(patterns) == 0:
            return PatternSelectionResult.none("No patterns are registered.")

        requirements = self.derive_requirements(task, model)
        rejections: list[str] = []
        candidates: list[tuple[IAgentPattern, int]] = []

        for pattern in patterns:
            satisfied, error = self._satisfies(pattern.descriptor, requirements)
            if not satisfied:
                rejections.append(f"{pattern.descriptor.pattern_id}: {error}")
                continue

            decision = self._policy.evaluate_pattern_selection(task, pattern.descriptor, model)
            if not decision.allowed:
                rejections.append(f"{pattern.descriptor.pattern_id}: {decision.reason}")
                continue

            candidates.append((pattern, self._score(pattern.descriptor, requirements, model)))

        if not candidates:
            return PatternSelectionResult.none("; ".join(rejections))

        if preferred_pattern_id:
            for candidate, _ in candidates:
                if candidate.descriptor.pattern_id == preferred_pattern_id:
                    return PatternSelectionResult.selected(candidate, requirements, rejections)

        candidates.sort(
            key=lambda c: (
                -c[1],
                int(c[0].descriptor.risk_level),
                c[0].descriptor.pattern_id,
            )
        )
        winner = candidates[0][0]
        return PatternSelectionResult.selected(winner, requirements, rejections)

    @staticmethod
    def _satisfies(
        descriptor: PatternDescriptor, requirement: PatternRequirement
    ) -> tuple[bool, str]:
        if requirement.needs_tools and not (
            descriptor.requires_tools or descriptor.requires_native_tool_calling
        ):
            return False, "task requires tools but pattern does not use them"
        if requirement.needs_memory and not descriptor.requires_memory:
            return False, "task requires memory but pattern does not consume an active context"
        if requirement.needs_multi_agent and not descriptor.supports_multi_agent:
            return False, "task requires multi-agent execution but pattern is single-agent"
        # needs_json_mode is intentionally a soft preference, not a hard reject.
        return True, ""

    @staticmethod
    def _score(
        descriptor: PatternDescriptor,
        requirement: PatternRequirement,
        model: ModelProfile,
    ) -> int:
        score = 0

        if descriptor.is_bounded:
            score += 4
        if descriptor.risk_level == PatternRiskLevel.LOW:
            score += 3
        elif descriptor.risk_level == PatternRiskLevel.MEDIUM:
            score += 1

        if (
            requirement.needs_validation
            and descriptor.pattern_id == known_pattern_ids.PLAN_EXECUTE_VALIDATE
        ):
            score += 5

        if requirement.needs_json_mode and descriptor.requires_json_mode:
            score += 2

        if (
            descriptor.requires_native_tool_calling
            and model.capabilities.supports_native_tool_calling
        ):
            score += 1

        if (
            not requirement.needs_tools
            and not descriptor.requires_tools
            and not descriptor.requires_native_tool_calling
        ):
            score += 2

        return score
