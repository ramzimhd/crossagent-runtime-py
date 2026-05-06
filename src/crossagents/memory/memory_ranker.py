"""Deterministic ranker."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from crossagents.abstractions.memory import MemoryItem


class MemoryRanker:
    """When all items already carry a score the ranker honours it; otherwise
    items are ranked by length-normalised lexical overlap with the query.

    Ties resolve on item id so ranking is reproducible across runs.
    """

    def rank(self, query: str, items: Sequence[MemoryItem]) -> tuple[MemoryItem, ...]:
        if items is None:
            raise ValueError("items must not be None")
        if not items:
            return ()

        if all(item.score is not None for item in items):
            return tuple(
                sorted(
                    items,
                    key=lambda i: (-(i.score or 0.0), i.id),
                )
            )

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return tuple(items)

        scored: list[tuple[MemoryItem, float]] = [
            (item, self._compute_overlap(query_tokens, item.content)) for item in items
        ]
        scored.sort(key=lambda t: (-t[1], t[0].id))
        return tuple(replace(item, score=score) for item, score in scored)

    @staticmethod
    def _compute_overlap(query_tokens: frozenset[str], content: str) -> float:
        content_tokens = MemoryRanker._tokenize(content)
        if not content_tokens:
            return 0.0
        hits = sum(1 for token in content_tokens if token in query_tokens)
        # Use ordered-equivalent: split() result preserves count of tokens; the
        # frozenset above deduplicates only for the membership query side.
        return hits / max(1, len(MemoryRanker._tokenize_list(content)))

    @staticmethod
    def _tokenize(text: str) -> frozenset[str]:
        return frozenset(MemoryRanker._tokenize_list(text))

    @staticmethod
    def _tokenize_list(text: str) -> list[str]:
        if not text or not text.strip():
            return []
        tokens: list[str] = []
        current: list[str] = []
        for ch in text:
            if ch.isalnum():
                current.append(ch)
            elif current:
                tokens.append("".join(current).lower())
                current = []
        if current:
            tokens.append("".join(current).lower())
        return tokens
