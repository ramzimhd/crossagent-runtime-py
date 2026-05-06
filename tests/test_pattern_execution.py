from __future__ import annotations

from crossagents.abstractions.agents import AgentState, AgentTask
from crossagents.abstractions.policy import AgentPolicy
from crossagents.patterns import NoToolPattern, PlanExecuteValidatePattern
from crossagents.testing import PatternTestHarness
from tests.fixtures import echo_adapter, scripted_adapter


async def test_no_tool_pattern_produces_deterministic_output() -> None:
    harness = PatternTestHarness(echo_adapter())
    harness.policy = AgentPolicy(require_validation=False)
    task = AgentTask(task_id="no-tool", input="ECHO ME", requires_validation=False)

    result = await harness.run(NoToolPattern(), task)

    assert result.state == AgentState.COMPLETED
    assert result.output == "ECHO ME"


async def test_plan_execute_validate_pattern_runs_three_phases_and_reports_validation() -> None:
    adapter = scripted_adapter(
        "scripted",
        "step 1; step 2; step 3",
        "the answer is 42",
        "PASS - looks complete",
    )
    harness = PatternTestHarness(adapter)
    task = AgentTask(task_id="pev", input="Compute the answer.", requires_validation=True)

    result = await harness.run(PlanExecuteValidatePattern(), task)

    assert result.state == AgentState.COMPLETED
    assert result.output == "the answer is 42"
    assert result.validation_passed is True
    assert len(adapter.calls) == 3


async def test_plan_execute_validate_pattern_flags_validation_failure_when_validator_reports_fail() -> None:
    adapter = scripted_adapter(
        "scripted",
        "plan",
        "answer",
        "FAIL - missing detail",
    )
    harness = PatternTestHarness(adapter)
    task = AgentTask(task_id="pev-fail", input="Compute.", requires_validation=True)

    result = await harness.run(PlanExecuteValidatePattern(), task)

    assert result.state == AgentState.COMPLETED
    assert result.validation_passed is False
