from __future__ import annotations

from crossagent.abstractions.agents import AgentTask, AgentTaskType
from crossagent.abstractions.policy import AgentPolicy
from crossagent.core import PatternSelector, RuntimePolicyEngine, known_pattern_ids
from crossagent.patterns import JsonPlanPattern, NoToolPattern, PlanExecuteValidatePattern
from tests.fixtures import echo_profile


def test_select_prefers_no_tool_pattern_when_validation_is_not_required() -> None:
    policy = RuntimePolicyEngine(AgentPolicy(require_validation=False))
    selector = PatternSelector(policy)
    patterns = [PlanExecuteValidatePattern(), NoToolPattern()]
    task = AgentTask(task_id="t-1", input="answer", requires_validation=False)

    result = selector.select(task, echo_profile(), patterns)

    assert result.has_selection
    assert result.pattern is not None
    assert result.pattern.descriptor.pattern_id == known_pattern_ids.NO_TOOL


def test_select_prefers_plan_execute_validate_when_validation_is_required() -> None:
    policy = RuntimePolicyEngine(AgentPolicy())
    selector = PatternSelector(policy)
    patterns = [NoToolPattern(), PlanExecuteValidatePattern()]
    task = AgentTask(task_id="t-2", input="validate this", requires_validation=True)

    result = selector.select(task, echo_profile(), patterns)

    assert result.has_selection
    assert result.pattern is not None
    assert result.pattern.descriptor.pattern_id == known_pattern_ids.PLAN_EXECUTE_VALIDATE


def test_select_respects_task_allow_list() -> None:
    policy = RuntimePolicyEngine(AgentPolicy())
    selector = PatternSelector(policy)
    patterns = [NoToolPattern(), PlanExecuteValidatePattern()]
    task = AgentTask(
        task_id="t-3",
        input="x",
        requires_validation=True,
        allowed_pattern_ids=frozenset({known_pattern_ids.NO_TOOL}),
    )

    result = selector.select(task, echo_profile(), patterns)

    assert result.has_selection
    assert result.pattern is not None
    assert result.pattern.descriptor.pattern_id == known_pattern_ids.NO_TOOL


def test_select_filters_by_model_capabilities() -> None:
    policy = RuntimePolicyEngine(AgentPolicy(require_validation=False))
    selector = PatternSelector(policy)
    patterns = [NoToolPattern(), JsonPlanPattern()]
    task = AgentTask(task_id="t-4", input="x", requires_validation=False)

    profile_without_json = echo_profile("noj", json_mode=False)
    result_without_json = selector.select(task, profile_without_json, patterns)
    assert result_without_json.has_selection
    assert result_without_json.pattern is not None
    assert result_without_json.pattern.descriptor.pattern_id == known_pattern_ids.NO_TOOL

    profile_with_json = echo_profile("withj", json_mode=True)
    plan_task = AgentTask(
        task_id="t-4-plan",
        input="plan",
        type=AgentTaskType.PLAN,
        requires_validation=False,
    )
    plan_result = selector.select(plan_task, profile_with_json, patterns)
    assert plan_result.has_selection
    assert plan_result.pattern is not None
    assert plan_result.pattern.descriptor.pattern_id == known_pattern_ids.JSON_PLAN
