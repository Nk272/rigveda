from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def _BuildLibsqlUrlWithToken(baseUrl: str, authToken: str) -> str:
    """Convert libsql URL to SQLAlchemy dialect 'sqlite+libsql://' and append authToken."""
    parsed = urlparse(baseUrl)
    queryParams = dict(parse_qsl(parsed.query))
    if authToken:
        queryParams["authToken"] = authToken
    newQuery = urlencode(queryParams)
    # Force SQLAlchemy dialect prefix
    scheme = "sqlite+libsql"
    return urlunparse((scheme, parsed.netloc, parsed.path, parsed.params, newQuery, parsed.fragment))


libsqlUrl = os.getenv("LIBSQL_URL")
libsqlToken = os.getenv("LIBSQL_AUTH_TOKEN", "")

if libsqlUrl:
    # Use Turso (libsql) when configured via environment
    DATABASE_URL = _BuildLibsqlUrlWithToken(libsqlUrl, libsqlToken)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
else:
    # Local fallback to SQLite file for development
    DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent.parent / 'hymn_vectors.db'}"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

print("Database engine initialized")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def GetDatabase():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
