"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import Sequence

from crossagents.abstractions.models import (
    ModelCapabilities,
    ModelFinishReason,
    ModelProfile,
    ModelProvider,
    ModelRequest,
    ModelResponse,
)
from crossagents.testing import FakeModelAdapter


def echo_profile(
    profile_id: str = "echo",
    tool_calling: bool = False,
    json_mode: bool = False,
) -> ModelProfile:
    return ModelProfile(
        profile_id=profile_id,
        display_name=profile_id,
        provider=ModelProvider.CUSTOM,
        capabilities=ModelCapabilities(
            provider_name="test",
            model_id=profile_id,
            supports_native_tool_calling=tool_calling,
            supports_json_mode=json_mode,
            supports_streaming=False,
            max_context_tokens=8192,
            is_local=True,
        ),
    )


def echo_adapter(profile_id: str = "echo") -> FakeModelAdapter:
    def responder(request: ModelRequest, _index: int) -> ModelResponse:
        return ModelResponse(content=request.prompt, finish_reason=ModelFinishReason.STOP)

    return FakeModelAdapter(echo_profile(profile_id), responder)


def scripted_adapter(profile_id: str, *responses: str) -> FakeModelAdapter:
    canned: Sequence[str] = responses

    def responder(_request: ModelRequest, index: int) -> ModelResponse:
        return ModelResponse(
            content=canned[min(index - 1, len(canned) - 1)],
            finish_reason=ModelFinishReason.STOP,
        )

    return FakeModelAdapter(echo_profile(profile_id), responder)
