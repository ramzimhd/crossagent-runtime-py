"""Deterministic in-memory ``IMemoryProvider``."""

from __future__ import annotations

import re
from collections.abc import Sequence

from crossagent.abstractions.memory import IMemoryProvider, MemoryItem, MemoryQuery


_TOKEN_SEPARATORS = re.compile(r"[\s\.,;:!\?]+")


class FakeMemoryProvider(IMemoryProvider):
    """Items are returned in the order they were added, filtered by query token overlap."""

    def __init__(self) -> None:
        self._items: list[MemoryItem] = []

    def add(self, item: MemoryItem) -> "FakeMemoryProvider":
        if item is None:
            raise ValueError("item must not be None")
        self._items.append(item)
        return self

    @property
    def items(self) -> tuple[MemoryItem, ...]:
        return tuple(self._items)

    async def search(self, query: MemoryQuery) -> Sequence[MemoryItem]:
        if query is None:
            raise ValueError("query must not be None")
        tokens = {t.lower() for t in _TOKEN_SEPARATORS.split(query.query) if t}

        matches: list[MemoryItem] = []
        for item in self._items:
            if not tokens or any(t in item.content.lower() for t in tokens):
                matches.append(item)
                if len(matches) >= query.limit:
                    break
        return tuple(matches)
