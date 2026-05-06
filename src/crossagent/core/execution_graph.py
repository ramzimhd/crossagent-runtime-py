"""A simple ordered graph of named steps used by patterns to record their phases."""

from __future__ import annotations


class ExecutionGraph:
    """The graph itself does not run anything - it captures declared phases and
    their order so patterns can emit consistent step events.
    """

    def __init__(self) -> None:
        self._steps: list[str] = []

    def add_step(self, name: str) -> "ExecutionGraph":
        if not name or not name.strip():
            raise ValueError("Step name must be non-empty.")
        if name in self._steps:
            raise RuntimeError(f"Step '{name}' already exists in the graph.")
        self._steps.append(name)
        return self

    @property
    def steps(self) -> tuple[str, ...]:
        return tuple(self._steps)

    def contains(self, name: str) -> bool:
        return name in self._steps
