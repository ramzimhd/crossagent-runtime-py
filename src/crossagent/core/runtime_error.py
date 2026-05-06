"""Structured runtime error returned in ``RuntimeResult``.

The class is named ``RuntimeErrorInfo`` rather than ``RuntimeError`` because the
latter shadows Python's built-in exception type.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class RuntimeErrorCode(IntEnum):
    """Categorises a ``RuntimeErrorInfo`` for callers that branch on it."""

    NONE = 0
    UNKNOWN_MODEL = 1
    NO_ELIGIBLE_PATTERN = 2
    PATTERN_REJECTED = 3
    PATTERN_NOT_REGISTERED = 4
    INVALID_CONFIGURATION = 5
    POLICY_DENIED = 6
    CANCELLED = 7
    EXECUTION_FAILED = 8


@dataclass(frozen=True, kw_only=True)
class RuntimeErrorInfo:
    """Errors are values, not exceptions; the runtime only raises for programmer mistakes."""

    code: RuntimeErrorCode
    message: str
    detail: str | None = None
