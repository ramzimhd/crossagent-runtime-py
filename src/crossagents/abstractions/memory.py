"""Memory layer contracts (items, queries, providers, active context)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, kw_only=True)
class MemoryItem:
    """A single retrievable memory record.

    ``score``, when supplied, is opaque to the runtime and is used only by
    ranker implementations.
    """

    id: str
    content: str
    score: float | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class MemoryQuery:
    """Search request issued to a memory provider."""

    query: str
    limit: int = 8
    filters: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class ActiveContext:
    """The compressed and ranked working context produced by the memory layer.

    Patterns consume this to ground a model call; they do not query memory
    directly.
    """

    items: Sequence[MemoryItem]
    estimated_tokens: int = 0


class IMemoryProvider(Protocol):
    """Read-side abstraction over a memory store.

    The framework does not own the memory store - applications plug in their
    own (vector DB, keyword index, in-memory list, etc.).
    """

    async def search(self, query: MemoryQuery) -> Sequence[MemoryItem]: ...
