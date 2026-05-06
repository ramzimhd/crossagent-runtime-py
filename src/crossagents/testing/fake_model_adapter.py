"""Deterministic, in-process model adapter for tests and examples."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from crossagents.abstractions.models import (
    IModelAdapter,
    ModelFinishReason,
    ModelProfile,
    ModelRequest,
    ModelResponse,
)
from crossagents.abstractions.tools import ToolCall


Responder = Callable[[ModelRequest, int], ModelResponse]


class FakeModelAdapter(IModelAdapter):
    """Tests supply a responder that turns each (request, call_number) pair into
    a canned response. The adapter records every call so assertions can inspect
    what happened.
    """

    def __init__(
        self,
        profile: ModelProfile,
        responder: Responder | str,
        tool_calls: Sequence[ToolCall] | None = None,
    ) -> None:
        if profile is None:
            raise ValueError("profile must not be None")
        if responder is None:
            raise ValueError("responder must not be None")
        self._profile = profile
        if isinstance(responder, str):
            content = responder
            calls = tuple(tool_calls) if tool_calls else ()

            def _const_responder(_req: ModelRequest, _idx: int) -> ModelResponse:
                return ModelResponse(
                    content=content,
                    tool_calls=calls,
                    finish_reason=ModelFinishReason.STOP,
                )

            self._responder: Responder = _const_responder
        else:
            self._responder = responder
        self._calls: list[ModelRequest] = []

    @property
    def profile(self) -> ModelProfile:
        return self._profile

    @property
    def calls(self) -> tuple[ModelRequest, ...]:
        return tuple(self._calls)

    async def complete(self, request: ModelRequest) -> ModelResponse:
        if request is None:
            raise ValueError("request must not be None")
        self._calls.append(request)
        return self._responder(request, len(self._calls))
