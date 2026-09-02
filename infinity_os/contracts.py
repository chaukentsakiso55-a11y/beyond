from dataclasses import dataclass, field, asdict
from typing import Any, Callable
import time, uuid

@dataclass
class ToolResult:
    ok: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    retryable: bool = False

@dataclass
class AgentStep:
    id: str
    title: str
    tool: str
    args: dict[str, Any]
    permission: str = ""
    status: str = "pending"
    result: dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentPlan:
    id: str
    request: str
    steps: list[AgentStep]
    created_at: float = field(default_factory=time.time)
    status: str = "planned"

@dataclass
class ToolSpec:
    name: str
    description: str
    permission: str
    handler: Callable[..., ToolResult]
    source: str = "core"
    tags: list[str] = field(default_factory=list)

@dataclass
class Notification:
    id: str
    title: str
    body: str
    level: str = "info"
    source: str = "Infinity Core"
    created_at: float = field(default_factory=time.time)
    read: bool = False

    @classmethod
    def create(cls, title, body, level="info", source="Infinity Core"):
        return cls(str(uuid.uuid4()), title, body, level, source)
