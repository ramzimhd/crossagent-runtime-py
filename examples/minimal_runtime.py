"""Smallest end-to-end demo of the CrossAgent Runtime.

The example uses a ``FakeModelAdapter`` so it never reaches a real LLM
provider; the goal is to show the wiring (model registration, pattern
registration, pattern selection, audit) rather than model behaviour.
"""

from __future__ import annotations

import asyncio
import sys

from crossagents.abstractions.agents import AgentTask, AgentTaskType
from crossagents.abstractions.models import (
    ModelCapabilities,
    ModelFinishReason,
    ModelProfile,
    ModelProvider,
    ModelRequest,
    ModelResponse,
)
from crossagents.core import AgentRuntime, RuntimeOptions
from crossagents.patterns import NoToolPattern, PlanExecuteValidatePattern
from crossagents.testing import FakeModelAdapter, InMemoryAuditSink


async def main() -> int:
    sink = InMemoryAuditSink()
    runtime = AgentRuntime(RuntimeOptions(audit_sink=sink))

    profile = ModelProfile(
        profile_id="demo-echo",
        display_name="Demo echo model",
        provider=ModelProvider.CUSTOM,
        capabilities=ModelCapabilities(
            provider_name="demo",
            model_id="echo",
            supports_streaming=False,
            max_context_tokens=8192,
            is_local=True,
        ),
    )

    def responder(_request: ModelRequest, call_index: int) -> ModelResponse:
        if call_index == 1:
            content = "1. read input\n2. emit reply"
        elif call_index == 2:
            content = "Hello from CrossAgent Runtime."
        else:
            content = "PASS - response addresses the task."
        return ModelResponse(content=content, finish_reason=ModelFinishReason.STOP)

    adapter = FakeModelAdapter(profile, responder)

    runtime.register_model(adapter).register_pattern(NoToolPattern()).register_pattern(
        PlanExecuteValidatePattern()
    )

    task = AgentTask(
        task_id="demo-1",
        type=AgentTaskType.GENERIC,
        input="Greet a developer who is just trying out the runtime.",
        requires_validation=True,
    )

    result = await runtime.run(task, profile.profile_id)

    print(f"Session     : {result.session_id}")
    print(f"Selected    : {result.selected_pattern_id} on {result.selected_model_id}")
    print(f"Success     : {result.success}")
    print(f"Output      : {result.agent.output if result.agent else None}")
    print(f"Validation  : {result.agent.validation_passed if result.agent else None}")
    print()
    print("Audit trail:")
    for evt in sink.events:
        print(f"  [{evt.timestamp.strftime('%H:%M:%S.%f')[:-3]}] {evt.kind.name} :: {evt.message}")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
