"""Compresses ranked memory items into an ``ActiveContext`` within a soft token budget."""

from __future__ import annotations

from collections.abc import Sequence

from crossagents.abstractions.memory import ActiveContext, MemoryItem


class ContextCompressor:
    """Uses a simple character-based estimator (~4 chars per token) to keep
    behaviour deterministic without pulling in a tokenizer.
    """

    _CHARS_PER_TOKEN = 4

    def __init__(self, max_tokens: int = 2048) -> None:
        if max_tokens <= 0:
            raise ValueError("Token budget must be positive.")
        self._max_tokens = max_tokens

    def compress(self, ranked: Sequence[MemoryItem]) -> ActiveContext:
        if ranked is None:
            raise ValueError("ranked must not be None")

        kept: list[MemoryItem] = []
        total_chars = 0
        budget = self._max_tokens * self._CHARS_PER_TOKEN

        for item in ranked:
            size = len(item.content)
            if total_chars + size > budget and kept:
                break
            kept.append(item)
            total_chars += size

        estimated_tokens = (total_chars + self._CHARS_PER_TOKEN - 1) // self._CHARS_PER_TOKEN
        return ActiveContext(items=tuple(kept), estimated_tokens=estimated_tokens)
