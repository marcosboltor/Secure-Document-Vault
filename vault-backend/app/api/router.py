from fastapi import APIRouter

from app.modules.users.presentation.api.users_router import router as users_router
from app.modules.files.presentation.api.files_router import router as files_router

api_router = APIRouter()

api_router.include_router(users_router, prefix="/users", tags=["Usuarios"])
api_router.include_router(files_router, prefix="/documents", tags=["Documentos"])
