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
    primary_deity_id: int = None
    deity_color: str = "#95A5A6"

class HymnNeighbor(BaseModel):
    id: str
    title: str
    book_number: int
    hymn_number: int
    deity_names: str
    deity_count: int
    hymn_score: float
    similarity: float
    primary_deity_id: int = None
    deity_color: str = "#95A5A6"
    summary: str = ""

class NodeResponse(BaseModel):
    node: HymnNode
    neighbors: List[HymnNeighbor]

class GraphResponse(BaseModel):
    nodes: List[HymnNode]
