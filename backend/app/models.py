from sqlalchemy import Column, String, Integer, Float, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class HymnVector(Base):
    __tablename__ = "hymn_vectors"
    
    hymn_id = Column(String, primary_key=True)
    book_number = Column(Integer)
    hymn_number = Column(Integer)
    title = Column(Text)
    deity_vector = Column(Text)
    deity_names = Column(Text)
    deity_count = Column(Integer)
    hymn_score = Column(Float)

class HymnSimilarity(Base):
    __tablename__ = "hymn_similarities_cosine"
    
    hymn1_id = Column(String, primary_key=True)
    hymn2_id = Column(String, primary_key=True)
    similarity = Column(Float)

class DeityIndex(Base):
    __tablename__ = "deity_index"
    
    deity_id = Column(Integer, primary_key=True)
    deity_name = Column(String, unique=True)
    vector_position = Column(Integer)
    deity_frequency = Column(Integer)
