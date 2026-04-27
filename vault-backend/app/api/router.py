from fastapi import APIRouter

from app.modules.users.presentation.api.users_router import router as users_router
from app.modules.files.presentation.api.files_router import router as files_router

router = APIRouter()

router.include_router(users_router, prefix="/users", tags=["Usuarios"])
router.include_router(files_router, prefix="/files", tags=["Documentos"])
