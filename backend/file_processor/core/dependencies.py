from typing import Generator, Optional

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.user import User


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(db: Session, token: str) -> Optional[User]:
    """Decode JWT token and return current user"""
    from ..core.security import decode_access_token
    
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    username: Optional[str] = payload.get("sub")
    if username is None:
        return None
    
    user = db.query(User).filter(User.username == username).first()
    return user
