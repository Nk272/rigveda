from pydantic import BaseModel
from typing import List

class HymnNode(BaseModel):
    id: str
    title: str
    book_number: int
    hymn_number: int
    deity_names: str
    deity_count: int
    hymn_score: float

class HymnNeighbor(BaseModel):
    id: str
    title: str
    book_number: int
    hymn_number: int
    deity_names: str
    deity_count: int
    hymn_score: float
    similarity: float

class NodeResponse(BaseModel):
    node: HymnNode
    neighbors: List[HymnNeighbor]

class GraphResponse(BaseModel):
    nodes: List[HymnNode]
