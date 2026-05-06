"""Pattern descriptor, requirement, services protocol, and the executable contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from crossagents.abstractions.agents import AgentContext, AgentResult
    from crossagents.abstractions.audit import IAuditSink
    from crossagents.abstractions.memory import IMemoryProvider
    from crossagents.abstractions.models import IModelAdapter
    from crossagents.abstractions.policy import AgentPolicy, IPolicyEngine
    from crossagents.abstractions.tools import IToolInvoker


class PatternRiskLevel(IntEnum):
    """Classifies the risk profile of an agent pattern.

    The runtime uses this to reject unsafe configurations (for example, an
    unbounded ReAct pattern) regardless of policy permissiveness.
    """

    LOW = 0
    MEDIUM = 1
    HIGH = 2
    UNBOUNDED = 3


@dataclass(frozen=True, kw_only=True)
class PatternDescriptor:
    """Static description of a pattern.

    This is what the selector inspects; patterns themselves are not invoked
    until one has been chosen.
    """

    pattern_id: str
    name: str
    requires_tools: bool = False
    requires_memory: bool = False
    requires_native_tool_calling: bool = False
    requires_json_mode: bool = False
    supports_multi_agent: bool = False
    is_bounded: bool = False
    max_steps: int = 0
    risk_level: PatternRiskLevel = PatternRiskLevel.LOW


@dataclass(frozen=True, kw_only=True)
class PatternRequirement:
    """Computed requirements for a single (task, model) pair.

    The selector compares these requirements against a candidate
    ``PatternDescriptor``.
    """

    needs_tools: bool = False
    needs_memory: bool = False
    needs_json_mode: bool = False
    needs_validation: bool = False
    needs_multi_agent: bool = False


class IPatternServices(Protocol):
    """Services exposed to a pattern during execution.

    Patterns must not reach outside this surface; doing so would couple them to
    a particular runtime build.
    """

    @property
    def session_id(self) -> str: ...

    @property
    def model(self) -> "IModelAdapter": ...

    @property
    def tools(self) -> "IToolInvoker | None": ...

    @property
    def memory(self) -> "IMemoryProvider | None": ...

    @property
    def audit(self) -> "IAuditSink": ...

    @property
    def policy(self) -> "IPolicyEngine": ...

    @property
    def effective_policy(self) -> "AgentPolicy": ...


class IAgentPattern(Protocol):
    """An executable agent pattern.

    Implementations are stateless; per-session state lives only in the
    ``AgentContext`` and in services scoped to the call.
    """

    @property
    def descriptor(self) -> PatternDescriptor: ...

    async def execute(
        self,
        context: "AgentContext",
        services: IPatternServices,
    ) -> "AgentResult": ...
