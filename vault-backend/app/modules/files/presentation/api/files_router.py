from typing import List
from fastapi import APIRouter, Depends, Header
from app.modules.files.presentation.schemas.files_schemas import FileResponse
from app.modules.files.application.use_cases.get_files_usecase import GetFilesUseCase
from app.modules.files.presentation.di.dependencies import get_files_usecase

router = APIRouter()


@router.get("/", response_model=List[FileResponse])
async def files(
    user_id: str = Header(..., description="ID del usuario para simular sesión"),
    use_case: GetFilesUseCase = Depends(get_files_usecase),
):
    """
    Endpoint para listar todos los archivos accesibles por el usuario.
    Para pruebas, se debe enviar el header 'user-id' (ej: 'user-001').
    """
    files = await use_case.execute(user_id)
    return files
