import enum
from datetime import datetime

from sqlmodel import Field, SQLModel


class AgentStatus(str, enum.Enum):
    running = "running"
    stopped = "stopped"
    error = "error"
    creating = "creating"


class NodeStatus(str, enum.Enum):
    online = "online"
    offline = "offline"


class Agent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    agent_type: str = "opencode"
    status: AgentStatus = AgentStatus.creating
    node_id: int | None = Field(default=None, foreign_key="node.id")
    project_id: int | None = Field(default=None, foreign_key="project.id")
    user_id: int | None = Field(default=None, foreign_key="user.id")
    cpu_required: float = 1.0
    memory_required: int = 512
    port: int | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Node(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    host: str
    port: int = 8082
    status: NodeStatus = NodeStatus.offline
    cpu_total: float = 0.0
    cpu_used: float = 0.0
    memory_total: int = 0
    memory_used: int = 0
    agent_count: int = 0
    labels: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
