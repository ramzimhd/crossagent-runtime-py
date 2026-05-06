"""A bounded FIFO buffer used to retain the most recent conversation turns."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from typing import Generic, TypeVar

T = TypeVar("T")


class SlidingMemoryBuffer(Generic[T]):
    """The buffer is intentionally simple and not thread-safe; share at most
    one buffer per session.
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("Capacity must be positive.")
        self._capacity = capacity
        self._items: deque[T] = deque(maxlen=capacity)

    @property
    def capacity(self) -> int:
        return self._capacity

    def __len__(self) -> int:
        return len(self._items)

    def add(self, item: T) -> None:
        # deque.maxlen handles the eviction.
        self._items.append(item)

    def clear(self) -> None:
        self._items.clear()

    def snapshot(self) -> tuple[T, ...]:
        return tuple(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(tuple(self._items))
