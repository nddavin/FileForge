from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...core.dependencies import get_db

router = APIRouter()


@router.get("/")
def get_files(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"files": []}
