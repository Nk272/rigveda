from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Always use the bundled SQLite database inside the image
DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent.parent / 'hymn_vectors.db'}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def GetDatabase():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def EnsureIndexes():
    conn = engine.connect()
    try:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_hymn_sim_h1 ON hymn_similarities_cosine(hymn1_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_hymn_sim_h2 ON hymn_similarities_cosine(hymn2_id)"))
    finally:
        conn.close()
