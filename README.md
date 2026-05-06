# CrossAgent Runtime (Python)

CrossAgent Runtime is a provider-agnostic, model-adaptive agent runtime for building controlled mono-agent and multi-agent systems on Python. It picks an execution pattern that fits a given task, model, policy, and operational constraints, then runs it inside an audited, bounded session.

This repository contains the Python implementation of the framework. Implementations in other ecosystems (.NET, TypeScript) live in separate repositories so each can follow the conventions and release cadence of its own ecosystem.

## What it is

- A small set of stable contracts (`crossagent.abstractions`) describing models, tools, memory, patterns, policy, and audit.
- A minimal runtime host (`crossagent.core`) that registers adapters and patterns, selects one for each task, runs it, and surfaces a structured result.
- A first-party set of safe patterns (`crossagent.patterns`): a no-tool single call, a Plan-Execute-Validate flow, a JSON plan skeleton, and a strictly bounded ReAct loop.
- Optional layers for tooling (`crossagent.tooling`) and memory (`crossagent.memory`) that can be plugged in independently.
- Deterministic test doubles (`crossagent.testing`) for pattern and runtime tests with no external dependencies.

## What it isn't

- Not a chatbot framework. Conversations are a use case applications can build on top, not the framework's purpose.
- Not coupled to a single LLM provider. The framework ships no provider adapters in this milestone; applications wire their own through `IModelAdapter`.
- Not a tool-calling library. Tooling is an optional module; tasks that don't need tools never see the tooling layer.
- Not a memory store. Memory retrieval is an optional module; the framework does not own a database or vector index.
- Not unbounded. Patterns must declare bounds. Unbounded ReAct configurations are rejected at registration time.

## Core concepts

- **Model adapter**: a thin `IModelAdapter` implementation that talks to one model and reports `ModelCapabilities`.
- **Agent task**: a single unit of work (`AgentTask`) with a type, input, and optional requirements.
- **Pattern**: an `IAgentPattern` plus a `PatternDescriptor` that declares its risk profile, bounds, and dependencies.
- **Pattern selector**: a deterministic chooser that filters patterns by task requirements, model capabilities, and policy, then scores survivors.
- **Policy engine**: an `IPolicyEngine` that translates declarative policies (`AgentPolicy`) into yes/no decisions for selection and tool calls.
- **Audit pipeline**: a per-session buffer that fans events out to `IAuditSink` and surfaces them in the runtime result.

## Minimal example

```python
import asyncio

from crossagent.abstractions.agents import AgentTask
from crossagent.abstractions.models import (
    ModelCapabilities, ModelProfile, ModelProvider,
)
from crossagent.core import AgentRuntime, RuntimeOptions
from crossagent.patterns import NoToolPattern, PlanExecuteValidatePattern
from crossagent.testing import FakeModelAdapter, InMemoryAuditSink


async def main() -> None:
    runtime = AgentRuntime(RuntimeOptions(audit_sink=InMemoryAuditSink()))

    profile = ModelProfile(
        profile_id="demo-echo",
        display_name="Demo echo model",
        provider=ModelProvider.CUSTOM,
        capabilities=ModelCapabilities(
            provider_name="demo", model_id="echo", is_local=True,
        ),
    )

    runtime.register_model(
        FakeModelAdapter(profile, "Hello from CrossAgent Runtime.")
    ).register_pattern(NoToolPattern()).register_pattern(PlanExecuteValidatePattern())

    result = await runtime.run(
        AgentTask(task_id="demo-1", input="Say hello.", requires_validation=False),
        profile.profile_id,
    )

    print(f"{result.selected_pattern_id}: {result.agent.output if result.agent else ''}")


if __name__ == "__main__":
    asyncio.run(main())
```

A self-contained runnable version of this lives in [examples/minimal_runtime.py](examples/minimal_runtime.py).

## Package layout

| Module | Purpose |
| --- | --- |
| `crossagent.abstractions` | Stable contracts (models, tools, memory, patterns, policy, audit) |
| `crossagent.core` | Runtime host, session, selector, default policy engine, audit pipeline |
| `crossagent.patterns` | First-party safe patterns |
| `crossagent.tooling` | Optional tool registry, validator, executor, normalizer |
| `crossagent.memory` | Optional retrieval, ranking, compression, sliding buffer |
| `crossagent.testing` | Deterministic test doubles |

## Design principles

1. **Provider-agnostic**: model behaviour reaches the runtime only through `IModelAdapter` and `ModelCapabilities`.
2. **Model-adaptive**: pattern selection inspects the model's capability profile and degrades safely when something is missing.
3. **Bounded by default**: every shipped pattern declares step counts and risk levels; the runtime rejects unbounded configurations.
4. **Optional middleware**: tooling and memory are separate modules and separate runtime services; they can be omitted entirely.
5. **Auditable**: every session emits a canonical sequence of audit events suitable for compliance and debugging.
6. **Deterministic to test**: `crossagent.testing` ships in-process fakes for every external dependency the framework defines.
7. **Small public surface**: contracts are short, immutable, and documented; framework code never exposes provider-specific types.

## Current status

This is the first milestone. It establishes the contracts, the runtime, three patterns plus a strictly bounded ReAct loop, optional tooling and memory layers, and the test surface. Provider adapters, multi-agent orchestration primitives, distributed session storage, and other extensions are out of scope for this milestone.

## What is intentionally not in this milestone

- No real provider adapters (OpenAI, Anthropic, Bedrock, Ollama, etc.).
- No vector store, embedding, or document extraction implementations.
- No multi-agent orchestration patterns (debate, swarm, voting). The contracts allow them; an implementation will arrive in a later milestone.
- No streaming response surface beyond the boolean capability flag.
- No long-term session persistence.
- No telemetry exporter (open-telemetry, Prometheus, etc.). The audit sink is the integration point.

## Building and testing

Using [uv](https://docs.astral.sh/uv/) (recommended):

```sh
uv sync --all-extras
uv run pytest
uv run python examples/minimal_runtime.py
uv build
```

Using `pip` and `python -m build`:

```sh
python -m pip install -e ".[test]"
pytest
python examples/minimal_runtime.py
python -m pip install build && python -m build
```

Tests run entirely in-process and require no credentials or network access.

## License

MIT. See [LICENSE](LICENSE).
