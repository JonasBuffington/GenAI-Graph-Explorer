# app\models\graph.py
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field

class MasteryStatus(str, Enum):
    UNSEEN = "UNSEEN"
    LEARNING = "LEARNING"
    MASTERED = "MASTERED"

class RelationshipType(str, Enum):
    PREREQUISITE = "PREREQUISITE"
    FOLLOW_UP = "FOLLOW_UP"
    ALTERNATIVE = "ALTERNATIVE"

class Node(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    mastery_status: MasteryStatus = MasteryStatus.UNSEEN
    galaxies: list[str] = []
    embedding: list[float] | None = Field(default=None, repr=False)

class Edge(BaseModel):
    source_id: UUID
    target_id: UUID
    label: RelationshipType

class Graph(BaseModel):
    nodes: list[Node]
    edges: list[Edge]

class NodeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    mastery_status: MasteryStatus | None = None
    galaxies: list[str] | None = None