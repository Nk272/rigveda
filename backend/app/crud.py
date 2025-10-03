from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List, Optional
from . import models, schemas

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

def GetHymnsByIds(db: Session, hymnIds: List[str]) -> List[models.HymnVector]:
    return db.query(models.HymnVector).filter(models.HymnVector.hymn_id.in_(hymnIds)).all()
