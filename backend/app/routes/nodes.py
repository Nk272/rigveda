from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..db import GetDatabase
import json
import os

router = APIRouter()

# Load summaries once at startup
SUMMARIES = {}
summaries_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'Data', 'JSONMaps', 'rigveda_summaries.json')
if os.path.exists(summaries_path):
    with open(summaries_path, 'r') as f:
        SUMMARIES = json.load(f)

@router.get("/nodes", response_model=schemas.GraphResponse)
def GetAllNodes(db: Session = Depends(GetDatabase)):
    """Get all hymn nodes with basic metadata"""
    hymns = crud.GetAllHymns(db)
    deity_colors = crud.GetDeityColors(db)

    nodes = [
        schemas.HymnNode(
            id=hymn.hymn_id,
            title=hymn.title,
            book_number=hymn.book_number,
            hymn_number=hymn.hymn_number,
            deity_names=hymn.deity_names or "",
            deity_count=hymn.deity_count or 0,
            hymn_score=hymn.hymn_score or 0.0,
            primary_deity_id=hymn.primary_deity_id,
            deity_color=deity_colors.get(hymn.primary_deity_id, "#95A5A6")
        )
        for hymn in hymns
    ]
    return schemas.GraphResponse(nodes=nodes)

@router.get("/graph/initial", response_model=schemas.GraphResponse)
def GetInitialGraph(db: Session = Depends(GetDatabase)):
    """Get all hymns for initial graph"""
    hymns = crud.GetAllHymns(db)
    deity_colors = crud.GetDeityColors(db)

    nodes = [
        schemas.HymnNode(
            id=hymn.hymn_id,
            title=hymn.title,
            book_number=hymn.book_number,
            hymn_number=hymn.hymn_number,
            deity_names=hymn.deity_names or "",
            deity_count=hymn.deity_count or 0,
            hymn_score=hymn.hymn_score or 0.0,
            primary_deity_id=hymn.primary_deity_id,
            deity_color=deity_colors.get(hymn.primary_deity_id, "#95A5A6")
        )
        for hymn in hymns
    ]
    return schemas.GraphResponse(nodes=nodes)

@router.get("/node/{hymnId}", response_model=schemas.NodeResponse)
def GetNodeWithNeighbors(hymnId: str, limit: int = 4, db: Session = Depends(GetDatabase)):
    """Get hymn node and its most similar neighbors with summaries"""
    # Get the main hymn
    hymn = crud.GetHymnById(db, hymnId)
    if not hymn:
        raise HTTPException(status_code=404, detail="Hymn not found")

    # Get deity colors
    deity_colors = crud.GetDeityColors(db)

    # Get diverse similar hymns (top 4 from different deities)
    similarHymns = crud.GetDiverseSimilarHymns(db, hymnId, limit)

    # Get the hymn data for neighbors
    neighborIds = [sim[0] for sim in similarHymns]
    neighborHymns = crud.GetHymnsByIds(db, neighborIds)
    
    # Create similarity lookup
    similarityLookup = {sim[0]: sim[1] for sim in similarHymns}
    
    # Build response
    node = schemas.HymnNode(
        id=hymn.hymn_id,
        title=hymn.title,
        book_number=hymn.book_number,
        hymn_number=hymn.hymn_number,
        deity_names=hymn.deity_names or "",
        deity_count=hymn.deity_count or 0,
        hymn_score=hymn.hymn_score or 0.0,
        primary_deity_id=hymn.primary_deity_id,
        deity_color=deity_colors.get(hymn.primary_deity_id, "#95A5A6")
    )
    
    neighbors = [
        schemas.HymnNeighbor(
            id=neighbor.hymn_id,
            title=neighbor.title,
            book_number=neighbor.book_number,
            hymn_number=neighbor.hymn_number,
            deity_names=neighbor.deity_names or "",
            deity_count=neighbor.deity_count or 0,
            hymn_score=neighbor.hymn_score or 0.0,
            similarity=similarityLookup[neighbor.hymn_id],
            primary_deity_id=neighbor.primary_deity_id,
            deity_color=deity_colors.get(neighbor.primary_deity_id, "#95A5A6"),
            summary=SUMMARIES.get(neighbor.hymn_id, "")
        )
        for neighbor in neighborHymns
    ]
    
    return schemas.NodeResponse(node=node, neighbors=neighbors)
