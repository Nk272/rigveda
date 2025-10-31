from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional, Dict, Tuple
from . import models

_SIMILAR_CACHE: Dict[Tuple[str, int], List[Tuple[str, float]]] = {}

def GetAllHymns(db: Session) -> List[models.HymnVector]:
    return db.query(models.HymnVector).order_by(models.HymnVector.book_number, models.HymnVector.hymn_number).all()

def GetTopHymnsByScore(db: Session, limit: int = 20) -> List[models.HymnVector]:
    return db.query(models.HymnVector).order_by(desc(models.HymnVector.hymn_score)).limit(limit).all()

def GetHymnById(db: Session, hymnId: str) -> Optional[models.HymnVector]:
    return db.query(models.HymnVector).filter(models.HymnVector.hymn_id == hymnId).first()

def GetSimilarHymns(db: Session, hymnId: str, limit: int = 8) -> List[tuple]:
    # Fetch from both sides separately to leverage individual indexes
    left = db.query(
        models.HymnSimilarity.hymn2_id.label("other_id"),
        models.HymnSimilarity.similarity
    ).filter(
        models.HymnSimilarity.hymn1_id == hymnId
    ).order_by(desc(models.HymnSimilarity.similarity)).limit(limit).all()

    right = db.query(
        models.HymnSimilarity.hymn1_id.label("other_id"),
        models.HymnSimilarity.similarity
    ).filter(
        models.HymnSimilarity.hymn2_id == hymnId
    ).order_by(desc(models.HymnSimilarity.similarity)).limit(limit).all()

    combined: Dict[str, float] = {}
    for oid, sim in left:
        if oid not in combined or sim > combined[oid]:
            combined[oid] = sim
    for oid, sim in right:
        if oid not in combined or sim > combined[oid]:
            combined[oid] = sim

    # Sort by similarity and take top N
    sorted_pairs = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [(oid, sim) for oid, sim in sorted_pairs]

def GetDiverseSimilarHymns(db: Session, hymnId: str, limit: int = 4) -> List[tuple]:
    """Get similar hymns from different deities for diversity"""
    cacheKey = (hymnId, limit)
    cached = _SIMILAR_CACHE.get(cacheKey)
    if cached is not None:
        return cached
    # Get the source hymn's deity
    sourceHymn = GetHymnById(db, hymnId)
    if not sourceHymn:
        return []

    sourceDeityId = sourceHymn.primary_deity_id

    # Get candidates using the optimized fetch
    pairs = GetSimilarHymns(db, hymnId, limit=50)
    candidateIds = [oid for oid, _ in pairs]
    similarityMap = {oid: sim for oid, sim in pairs}

    # Get hymns with their deities
    candidateHymns = GetHymnsByIds(db, candidateIds)

    # Filter to get diverse deities
    result = []
    usedDeities = {}  # Don't include same deity as source

    for hymn in candidateHymns:
        if hymn.primary_deity_id not in usedDeities:
            result.append((hymn.hymn_id, similarityMap[hymn.hymn_id]))
            # usedDeities.add(hymn.primary_deity_id)
            if len(result) >= limit:
                break

    # If we don't have enough diverse hymns, fill with any remaining similar hymns
    if len(result) < limit:
        for hymn in candidateHymns:
            if hymn.hymn_id not in [r[0] for r in result]:
                result.append((hymn.hymn_id, similarityMap[hymn.hymn_id]))
                if len(result) >= limit:
                    break

    _SIMILAR_CACHE[cacheKey] = result
    return result

def GetHymnsByIds(db: Session, hymnIds: List[str]) -> List[models.HymnVector]:
    return db.query(models.HymnVector).filter(models.HymnVector.hymn_id.in_(hymnIds)).all()

def GetDeityColors(db: Session) -> Dict[int, str]:
    """Get mapping of deity_id to color"""
    deities = db.query(models.DeityIndex.deity_id, models.DeityIndex.deity_color).all()
    return {deity_id: color for deity_id, color in deities if color}

def GetTopNDeities(db: Session, n: int = 20) -> List[int]:
    """Get top N deities by number of hymns assigned (primary_deity_id)"""
    from sqlalchemy import func

    # Get deities ordered by count of hymns where they are the primary deity
    result = db.query(
        models.HymnVector.primary_deity_id,
        func.count(models.HymnVector.hymn_id).label('hymn_count')
    ).filter(
        models.HymnVector.primary_deity_id.isnot(None)
    ).group_by(
        models.HymnVector.primary_deity_id
    ).order_by(
        desc('hymn_count')
    ).limit(n).all()

    return [deity_id for deity_id, count in result]

def GetHymnsByDeities(db: Session, deityIds: List[int]) -> List[models.HymnVector]:
    """Get all hymns that belong to the specified deities"""
    return db.query(models.HymnVector).filter(models.HymnVector.primary_deity_id.in_(deityIds)).order_by(models.HymnVector.book_number, models.HymnVector.hymn_number).all()

def GetDeityStats(db: Session) -> List[Dict]:
    """Get statistics for all deities including hymn count"""
    deities = db.query(
        models.DeityIndex.deity_id,
        models.DeityIndex.deity_name,
        models.DeityIndex.deity_color,
        models.DeityIndex.deity_frequency
    ).order_by(desc(models.DeityIndex.deity_frequency)).all()

    return [
        {
            "deity_id": d.deity_id,
            "deity_name": d.deity_name,
            "deity_color": d.deity_color,
            "hymn_count": d.deity_frequency
        }
        for d in deities if d.deity_color  # Only include deities with colors
    ]

def GetHymnLightByDeities(db: Session, deityIds: List[int]):
    rows = db.query(
        models.HymnVector.hymn_id,
        models.HymnVector.title,
        models.HymnVector.book_number,
        models.HymnVector.hymn_number,
        models.HymnVector.primary_deity_id,
        models.HymnVector.word_count,
    ).filter(
        models.HymnVector.primary_deity_id.in_(deityIds)
    ).order_by(
        models.HymnVector.book_number, models.HymnVector.hymn_number
    ).all()
    return rows
