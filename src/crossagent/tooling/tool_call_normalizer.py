"""Canonicalises a ``ToolCall`` so downstream validators and tools see consistent input."""

from __future__ import annotations

import json
import uuid
from dataclasses import replace

from crossagent.abstractions.tools import ToolCall


class ToolCallNormalizer:
    """Trims tool names, defaults missing call ids, and rewrites empty argument
    payloads to the empty object literal "{}".
    """

    def normalize(self, call: ToolCall) -> ToolCall:
        if call is None:
            raise ValueError("call must not be None")

        name = (call.tool_name or "").strip()
        call_id = (call.call_id or "").strip()
        if not call_id:
            call_id = uuid.uuid4().hex

        args = (call.arguments_json or "").strip()
        if not args:
            args = "{}"

        # Best-effort canonical JSON: re-serialise valid JSON to drop whitespace;
        # leave invalid input untouched so the validator can surface the parse error.
        try:
            args = json.dumps(json.loads(args), separators=(",", ":"), ensure_ascii=False)
        except json.JSONDecodeError:
            pass

        return replace(call, call_id=call_id, tool_name=name, arguments_json=args)
