from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent.parent / 'hymn_vectors.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def GetDatabase():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
