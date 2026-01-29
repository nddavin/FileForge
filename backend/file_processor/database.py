from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .core.config import settings


engine = create_engine(
    settings.database_url,
    connect_args=(
        {"check_same_thread": False} if "sqlite" in settings.database_url else {}
    ),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session (compatible helper for imports).

    Many modules import `get_db` from `backend.file_processor.database`.
    Provide a lightweight generator here so those imports succeed and
    FastAPI can use it as a dependency.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
