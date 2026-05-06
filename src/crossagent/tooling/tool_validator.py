"""Lightweight validator for tool call arguments."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass

from crossagent.abstractions.tools import ToolCall, ToolDefinition


@dataclass(frozen=True, kw_only=True)
class ToolValidationResult:
    """Outcome of validating a ``ToolCall`` against a ``ToolDefinition``."""

    is_valid: bool
    reason: str | None = None
    issues: tuple[str, ...] = ()

    @staticmethod
    def valid() -> "ToolValidationResult":
        return ToolValidationResult(is_valid=True)

    @staticmethod
    def invalid(reason: str, issues: Sequence[str] | None = None) -> "ToolValidationResult":
        return ToolValidationResult(
            is_valid=False,
            reason=reason,
            issues=tuple(issues) if issues else (),
        )


_JSON_TYPE_TO_PY = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
    "null": (type(None),),
}


class ToolValidator:
    """The validator parses ``ToolCall.arguments_json`` as JSON and, when the
    tool's parameter schema is the canonical "object" form with declared
    properties, checks presence of required keys and basic type compatibility.

    It is intentionally permissive: applications that need full JSON Schema
    validation should plug in a richer implementation.
    """

    def validate(self, definition: ToolDefinition, call: ToolCall) -> ToolValidationResult:
        if definition is None:
            raise ValueError("definition must not be None")
        if call is None:
            raise ValueError("call must not be None")

        if definition.name != call.tool_name:
            return ToolValidationResult.invalid(
                f"Call targets '{call.tool_name}' but definition is for '{definition.name}'."
            )

        raw_args = call.arguments_json.strip() if call.arguments_json else ""
        try:
            args_obj = json.loads(raw_args if raw_args else "{}")
        except json.JSONDecodeError as ex:
            return ToolValidationResult.invalid("Arguments are not valid JSON.", [str(ex)])

        try:
            schema = json.loads(definition.parameters_json_schema)
        except json.JSONDecodeError:
            if isinstance(args_obj, dict):
                return ToolValidationResult.valid()
            return ToolValidationResult.invalid("Arguments must be a JSON object.")

        if not isinstance(args_obj, dict):
            return ToolValidationResult.invalid("Arguments must be a JSON object.")
        if not isinstance(schema, dict):
            return ToolValidationResult.valid()

        required = schema.get("required")
        if isinstance(required, list):
            missing = [
                f"missing required property '{name}'"
                for name in required
                if isinstance(name, str) and name not in args_obj
            ]
            if missing:
                return ToolValidationResult.invalid(
                    "Required properties are missing.",
                    missing,
                )

        properties = schema.get("properties")
        if isinstance(properties, dict):
            issues: list[str] = []
            for arg_name, arg_value in args_obj.items():
                prop_schema = properties.get(arg_name)
                if not isinstance(prop_schema, dict):
                    continue
                declared = prop_schema.get("type")
                if not isinstance(declared, str):
                    continue
                if not self._is_compatible(declared, arg_value):
                    issues.append(
                        f"property '{arg_name}' expected '{declared}' but got '{type(arg_value).__name__}'"
                    )
            if issues:
                return ToolValidationResult.invalid(
                    "One or more properties have incompatible types.",
                    issues,
                )

        return ToolValidationResult.valid()

    @staticmethod
    def _is_compatible(declared_type: str, value: object) -> bool:
        py_types = _JSON_TYPE_TO_PY.get(declared_type)
        if py_types is None:
            return True
        if declared_type == "boolean":
            return isinstance(value, bool)
        if declared_type in ("number", "integer") and isinstance(value, bool):
            return False
        return isinstance(value, py_types)
