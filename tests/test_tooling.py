from __future__ import annotations

from crossagent.abstractions.tools import ToolCall
from crossagent.testing import FakeTool
from crossagent.tooling import ToolRegistry


async def test_registry_rejects_unknown_tool() -> None:
    registry = ToolRegistry()

    result = await registry.invoke(
        ToolCall(call_id="1", tool_name="does-not-exist", arguments_json="{}")
    )

    assert result.success is False
    assert result.error is not None
    assert "Unknown tool" in result.error


async def test_registry_rejects_invalid_arguments_when_schema_requires_properties() -> None:
    schema = '{"type": "object", "properties": {"n": {"type": "number"}}, "required": ["n"]}'
    registry = ToolRegistry()
    registry.register(FakeTool("add", "Adds 1 to n.", schema))

    missing = await registry.invoke(
        ToolCall(call_id="1", tool_name="add", arguments_json="{}")
    )
    assert missing.success is False
    assert missing.error is not None
    assert "Required properties" in missing.error

    wrong_type = await registry.invoke(
        ToolCall(call_id="2", tool_name="add", arguments_json='{"n": "not-a-number"}')
    )
    assert wrong_type.success is False
    assert wrong_type.error is not None
    assert "incompatible types" in wrong_type.error

    ok = await registry.invoke(
        ToolCall(call_id="3", tool_name="add", arguments_json='{"n": 5}')
    )
    assert ok.success is True


async def test_registry_rejects_malformed_json() -> None:
    registry = ToolRegistry()
    registry.register(FakeTool("noop", "noop", '{"type": "object"}'))

    result = await registry.invoke(
        ToolCall(call_id="1", tool_name="noop", arguments_json="{ this is not json")
    )

    assert result.success is False
