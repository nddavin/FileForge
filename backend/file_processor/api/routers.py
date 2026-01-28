from fastapi import APIRouter

from .v1.auth import router as auth_router
from .v1.files import router as files_router
from .v1.integrations import router as integrations_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(files_router, prefix="/files", tags=["files"])
api_router.include_router(integrations_router, prefix="/integrations", tags=["integrations"])
