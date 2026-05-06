"""Stable contracts shared by the runtime, patterns, tooling, and memory."""

from crossagents.abstractions.agents import (
    AgentContext,
    AgentResult,
    AgentState,
    AgentTask,
    AgentTaskType,
)
from crossagents.abstractions.audit import AuditEvent, AuditEventKind, IAuditSink
from crossagents.abstractions.memory import (
    ActiveContext,
    IMemoryProvider,
    MemoryItem,
    MemoryQuery,
)
from crossagents.abstractions.models import (
    IModelAdapter,
    ModelCapabilities,
    ModelFinishReason,
    ModelProfile,
    ModelProvider,
    ModelRequest,
    ModelResponse,
)
from crossagents.abstractions.patterns import (
    IAgentPattern,
    IPatternServices,
    PatternDescriptor,
    PatternRequirement,
    PatternRiskLevel,
)
from crossagents.abstractions.policy import AgentPolicy, IPolicyEngine, PolicyDecision
from crossagents.abstractions.tools import (
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
