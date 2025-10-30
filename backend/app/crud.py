from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional, Dict
from . import models

def GetAllHymns(db: Session) -> List[models.HymnVector]:
    return db.query(models.HymnVector).order_by(models.HymnVector.book_number, models.HymnVector.hymn_number).all()

def GetTopHymnsByScore(db: Session, limit: int = 20) -> List[models.HymnVector]:
    return db.query(models.HymnVector).order_by(desc(models.HymnVector.hymn_score)).limit(limit).all()

def GetHymnById(db: Session, hymnId: str) -> Optional[models.HymnVector]:
    return db.query(models.HymnVector).filter(models.HymnVector.hymn_id == hymnId).first()

def GetSimilarHymns(db: Session, hymnId: str, limit: int = 8) -> List[tuple]:
    # Query similarities where hymnId is hymn1_id or hymn2_id
    similarities = db.query(
        models.HymnSimilarity.hymn1_id,
        models.HymnSimilarity.hymn2_id,
        models.HymnSimilarity.similarity
    ).filter(
        or_(
            models.HymnSimilarity.hymn1_id == hymnId,
            models.HymnSimilarity.hymn2_id == hymnId
        )
    ).order_by(desc(models.HymnSimilarity.similarity)).limit(limit).all()

    # Extract the other hymn IDs and similarities
    result = []
    for sim in similarities:
        otherHymnId = sim.hymn2_id if sim.hymn1_id == hymnId else sim.hymn1_id
        result.append((otherHymnId, sim.similarity))

    return result

def GetDiverseSimilarHymns(db: Session, hymnId: str, limit: int = 4) -> List[tuple]:
    """Get similar hymns from different deities for diversity"""
    # Get the source hymn's deity
    sourceHymn = GetHymnById(db, hymnId)
    if not sourceHymn:
        return []

    sourceDeityId = sourceHymn.primary_deity_id

    # Query all similarities
    similarities = db.query(
        models.HymnSimilarity.hymn1_id,
        models.HymnSimilarity.hymn2_id,
        models.HymnSimilarity.similarity
    ).filter(
        or_(
            models.HymnSimilarity.hymn1_id == hymnId,
            models.HymnSimilarity.hymn2_id == hymnId
        )
    ).order_by(desc(models.HymnSimilarity.similarity)).limit(100).all()

    # Extract hymn IDs
    candidateIds = []
    similarityMap = {}
    for sim in similarities:
        otherHymnId = sim.hymn2_id if sim.hymn1_id == hymnId else sim.hymn1_id
        candidateIds.append(otherHymnId)
        similarityMap[otherHymnId] = sim.similarity

    # Get hymns with their deities
    candidateHymns = GetHymnsByIds(db, candidateIds)

    # Filter to get diverse deities
    result = []
    usedDeities = {sourceDeityId}  # Don't include same deity as source

    for hymn in candidateHymns:
        if hymn.primary_deity_id not in usedDeities:
            result.append((hymn.hymn_id, similarityMap[hymn.hymn_id]))
            usedDeities.add(hymn.primary_deity_id)
            if len(result) >= limit:
                break

    # If we don't have enough diverse hymns, fill with any remaining similar hymns
    if len(result) < limit:
        for hymn in candidateHymns:
            if hymn.hymn_id not in [r[0] for r in result]:
                result.append((hymn.hymn_id, similarityMap[hymn.hymn_id]))
                if len(result) >= limit:
                    break

    return result

def GetHymnsByIds(db: Session, hymnIds: List[str]) -> List[models.HymnVector]:
    return db.query(models.HymnVector).filter(models.HymnVector.hymn_id.in_(hymnIds)).all()

def GetDeityColors(db: Session) -> Dict[int, str]:
    """Get mapping of deity_id to color"""
    deities = db.query(models.DeityIndex.deity_id, models.DeityIndex.deity_color).all()
    return {deity_id: color for deity_id, color in deities if color}
