from fastapi import APIRouter

from .v1.auth import router as auth_router
from .v1.files import router as files_router
from .v1.integrations import router as integrations_router
from .v1.rbac import router as rbac_router
from .v1.bulk_operations import router as bulk_operations_router
from .v1.sermons import router as sermons_router
from .v1.tasks import router as tasks_router
from .v1.storage import router as storage_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(files_router, prefix="/files", tags=["files"])
api_router.include_router(
    integrations_router, prefix="/integrations", tags=["integrations"]
)
api_router.include_router(rbac_router, prefix="/rbac", tags=["RBAC"])
api_router.include_router(sermons_router, prefix="/sermons", tags=["Sermons"])
api_router.include_router(bulk_operations_router, prefix="/bulk", tags=["Bulk Operations"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(storage_router, prefix="/storage", tags=["Storage"])
