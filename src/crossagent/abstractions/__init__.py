"""Stable contracts shared by the runtime, patterns, tooling, and memory."""

from crossagent.abstractions.agents import (
    AgentContext,
    AgentResult,
    AgentState,
    AgentTask,
    AgentTaskType,
)
from crossagent.abstractions.audit import AuditEvent, AuditEventKind, IAuditSink
from crossagent.abstractions.memory import (
    ActiveContext,
    IMemoryProvider,
    MemoryItem,
    MemoryQuery,
)
from crossagent.abstractions.models import (
    IModelAdapter,
    ModelCapabilities,
    ModelFinishReason,
    ModelProfile,
    ModelProvider,
    ModelRequest,
    ModelResponse,
)
from crossagent.abstractions.patterns import (
    IAgentPattern,
    IPatternServices,
    PatternDescriptor,
    PatternRequirement,
    PatternRiskLevel,
)
from crossagent.abstractions.policy import AgentPolicy, IPolicyEngine, PolicyDecision
from crossagent.abstractions.tools import (
    ITool,
    IToolInvoker,
    ToolCall,
    ToolDefinition,
    ToolPolicy,
    ToolResult,
)

__all__ = [
    "ActiveContext",
    "AgentContext",
    "AgentPolicy",
    "AgentResult",
    "AgentState",
    "AgentTask",
    "AgentTaskType",
    "AuditEvent",
    "AuditEventKind",
    "IAgentPattern",
    "IAuditSink",
    "IMemoryProvider",
    "IModelAdapter",
    "IPatternServices",
    "IPolicyEngine",
    "ITool",
    "IToolInvoker",
    "MemoryItem",
    "MemoryQuery",
    "ModelCapabilities",
    "ModelFinishReason",
    "ModelProfile",
    "ModelProvider",
    "ModelRequest",
    "ModelResponse",
    "PatternDescriptor",
    "PatternRequirement",
    "PatternRiskLevel",
    "PolicyDecision",
    "ToolCall",
    "ToolDefinition",
    "ToolPolicy",
    "ToolResult",
]
