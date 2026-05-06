"""Thin wrapper around an ``IMemoryProvider`` enforcing query validation."""

from __future__ import annotations

from collections.abc import Sequence

from crossagents.abstractions.memory import IMemoryProvider, MemoryItem, MemoryQuery


class MemoryRetriever:
    """Patterns must use a retriever rather than calling the provider directly
    so cross-cutting concerns (limits, normalisation) live in one place.
    """

    def __init__(self, provider: IMemoryProvider) -> None:
        if provider is None:
            raise ValueError("provider must not be None")
        self._provider = provider

    async def retrieve(self, query: MemoryQuery) -> Sequence[MemoryItem]:
        if query is None:
            raise ValueError("query must not be None")
        if not query.query or not query.query.strip():
            return ()
        if query.limit <= 0:
            return ()
        result = await self._provider.search(query)
        return result if result is not None else ()
