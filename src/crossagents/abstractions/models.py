"""Model-side contracts (profile, capabilities, request/response, adapter protocol)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from crossagents.abstractions.tools import ToolCall, ToolDefinition


class ModelProvider(IntEnum):
    """Identifies the broad category of model provider behind a ``ModelProfile``.

    The framework does not ship adapters for any specific provider; this enum
    exists only so policy and selection logic can reason about provenance.
    """

    UNKNOWN = 0
    OPEN_AI = 1
    ANTHROPIC = 2
    GOOGLE = 3
    MISTRAL = 4
    AZURE_OPEN_AI = 5
    BEDROCK = 6
    LOCAL = 7
    CUSTOM = 8


class ModelFinishReason(IntEnum):
    """Reason an adapter returned, in provider-neutral terms."""

    UNKNOWN = 0
    STOP = 1
    LENGTH = 2
    TOOL_CALLS = 3
    CONTENT_FILTER = 4
    ERROR = 5


@dataclass(frozen=True, kw_only=True)
class ModelCapabilities:
    """Declarative capability descriptor for a model.

    The runtime uses these flags to decide which patterns are eligible for a
    given task and model combination. All values default to a conservative
    "unsupported" state so unknown models degrade safely.
    """

    provider_name: str = ""
    model_id: str = ""
    supports_native_tool_calling: bool = False
    supports_json_mode: bool = False
    supports_json_schema: bool = False
    supports_vision: bool = False
    supports_streaming: bool = False
    max_context_tokens: int = 0
    is_local: bool = False


@dataclass(frozen=True, kw_only=True)
class ModelProfile:
    """A registered model description.

    The ``profile_id`` is the stable identifier applications use to request a
    specific model when running a task; the ``capabilities`` drive pattern
    selection.
    """

    profile_id: str
    display_name: str
    capabilities: ModelCapabilities
    provider: ModelProvider = ModelProvider.UNKNOWN
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class ModelRequest:
    """Provider-neutral request submitted to an ``IModelAdapter``."""

    prompt: str
    system: str | None = None
    tools: Sequence["ToolDefinition"] = ()
    json_schema: str | None = None
    json_mode: bool = False
    max_output_tokens: int | None = None
    temperature: float | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class ModelResponse:
    """Provider-neutral response returned from an ``IModelAdapter``.

    Adapters MUST populate ``tool_calls`` only when the underlying provider
    produced tool/function calls; the runtime never infers tool calls from
    prose.
    """

    content: str = ""
    tool_calls: Sequence["ToolCall"] = ()
    finish_reason: ModelFinishReason = ModelFinishReason.UNKNOWN
    metadata: Mapping[str, str] = field(default_factory=dict)


class IModelAdapter(Protocol):
    """A provider-neutral entry point to a single model.

    Implementations are expected to be thread-safe and stateless aside from any
    caching they choose to perform internally.
    """

    @property
    def profile(self) -> ModelProfile: ...

    async def complete(self, request: ModelRequest) -> ModelResponse: ...
