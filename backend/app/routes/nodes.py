from fastapi import APIRouter, Depends, HTTPException, Response
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
            deity_color=deity_colors.get(hymn.primary_deity_id, "#95A5A6"),
            word_count=getattr(hymn, 'word_count', None) or 0
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
            deity_color=deity_colors.get(hymn.primary_deity_id, "#95A5A6"),
            word_count=getattr(hymn, 'word_count', None) or 0
        )
        for hymn in hymns
    ]
    return schemas.GraphResponse(nodes=nodes)

@router.get("/graph/by-deities", response_model=schemas.GraphResponse)
def GetGraphByTopDeities(n: int = 20, db: Session = Depends(GetDatabase)):
    """Get hymns filtered by top N deities"""
    # Get top N deities
    topDeityIds = crud.GetTopNDeities(db, n)

    # Get hymns for these deities
    hymns = crud.GetHymnsByDeities(db, topDeityIds)
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
            deity_color=deity_colors.get(hymn.primary_deity_id, "#95A5A6"),
            word_count=getattr(hymn, 'word_count', None) or 0
        )
        for hymn in hymns
    ]
    return schemas.GraphResponse(nodes=nodes)

@router.get("/graph/light-by-deities", response_model=schemas.GraphLightResponse)
def GetLightGraphByTopDeities(n: int = 20, response: Response = None, db: Session = Depends(GetDatabase)):
    topDeityIds = crud.GetTopNDeities(db, n)
    hymns = crud.GetHymnLightByDeities(db, topDeityIds)
    deity_colors = crud.GetDeityColors(db)

    nodes = [
        schemas.HymnLightNode(
            id=h[0],
            title=h[1],
            book_number=h[2],
            hymn_number=h[3],
            primary_deity_id=h[4],
            deity_color=deity_colors.get(h[4], "#95A5A6"),
            word_count=h[5] or 0
        )
        for h in hymns
    ]

    if response is not None:
        response.headers["Cache-Control"] = "public, max-age=600"

    return schemas.GraphLightResponse(nodes=nodes)

@router.get("/deities/stats")
def GetDeityStatistics(db: Session = Depends(GetDatabase)):
    """Get statistics about deities"""
    return crud.GetDeityStats(db)

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
        deity_color=deity_colors.get(hymn.primary_deity_id, "#95A5A6"),
        word_count=getattr(hymn, 'word_count', None) or 0
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
            summary=SUMMARIES.get(neighbor.hymn_id, ""),
            word_count=getattr(neighbor, 'word_count', None) or 0
        )
        for neighbor in neighborHymns
    ]
    
    return schemas.NodeResponse(node=node, neighbors=neighbors)
