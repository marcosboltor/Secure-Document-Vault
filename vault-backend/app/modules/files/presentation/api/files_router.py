import base64
from typing import List
from fastapi import APIRouter, Depends, Path
from app.modules.files.presentation.schemas.files_schemas import (
    FileListResponse,
    FileDetailResponse,
    FileUploadRequest,
    DeleteResponse,
)
from app.modules.files.application.use_cases.get_files_usecase import GetFilesUseCase
from app.modules.files.application.use_cases.get_file_details_usecase import (
    GetFileDetailsUseCase,
)
from app.modules.files.application.use_cases.upload_file_usecase import (
    UploadFileUseCase,
)
from app.modules.files.application.use_cases.delete_file_usecase import (
    DeleteFileUseCase,
)
from app.modules.files.presentation.di.dependencies import (
    get_files_usecase,
    get_file_details_usecase,
    upload_file_usecase,
    delete_file_usecase,
)
from app.modules.users.presentation.di.dependencies import (
    get_current_user_id,
    get_current_user,
)
from app.modules.users.domain.entities.user import User

router = APIRouter()


@router.get("/", response_model=List[FileListResponse])
async def list_files(
    user_id: str = Depends(get_current_user_id),
    use_case: GetFilesUseCase = Depends(get_files_usecase),
):
    """
    Endpoint para listar todos los archivos accesibles por el usuario.
    Protegido por JWT.
    """
    files = await use_case.execute(user_id)
    return files


@router.get("/{file_id}", response_model=FileDetailResponse)
async def get_file_details(
    file_id: str = Path(..., description="ID del archivo"),
    user_id: str = Depends(get_current_user_id),
    use_case: GetFileDetailsUseCase = Depends(get_file_details_usecase),
):
    """
    Endpoint para obtener los detalles de un archivo por su ID.
    Verifica que el usuario tenga acceso (propietario o destinatario).
    Protegido por JWT.
    """
    file = await use_case.execute(file_id, user_id)

    # Codificar encrypted_content a base64 para la respuesta JSON
    encrypted_b64 = None
    if file.encrypted_content is not None:
        encrypted_b64 = base64.b64encode(file.encrypted_content).decode("utf-8")
    return FileDetailResponse(
        id=file.id,
        name=file.name,
        owner_id=file.owner_id,
        owner_name=file.owner_name,
        recipients=file.recipients,
        created_at=file.created_at,
        signer_public_key_base64=file.signer_public_key_base64,
        size=file.size,
        encrypted_content=encrypted_b64,
    )


@router.post("/", response_model=FileListResponse, status_code=201)
async def upload_file(
    request: FileUploadRequest,
    current_user: User = Depends(get_current_user),
    use_case: UploadFileUseCase = Depends(upload_file_usecase),
):
    """
    Endpoint para subir un nuevo archivo al vault.
    El campo encrypted_content debe enviarse como cadena codificada en base64.
    Protegido por JWT.
    """
    # Decodificar el contenido base64 a bytes
    encrypted_bytes = base64.b64decode(request.encrypted_content)

    # Extraer metadatos excluyendo ciphertext
    metadata = request.model_dump(exclude={"encrypted_content"})
    # Asignar datos del usuario autenticado automáticamente
    metadata["owner_id"] = current_user.id
    metadata["owner_name"] = current_user.username
    metadata["signer_public_key_base64"] = current_user.public_signing_key

    saved_file = await use_case.execute(metadata=metadata, binary_blob=encrypted_bytes)

    # Construir la entidad de dominio
    """
    vault_file = VaultFile(
        id=str(uuid.uuid4()),
        name=request.name,
        owner_id=request.owner_id,
        owner_name=request.owner_name,
        recipients=request.recipients,
        created_at=datetime.utcnow(),
        signer_public_key_base64=request.signer_public_key_base64,
        encrypted_content=encrypted_bytes,
    )
    """
    # saved_file = await use_case.execute(vault_file)
    return saved_file


@router.delete("/{file_id}", response_model=DeleteResponse)
async def delete_file(
    file_id: str = Path(..., description="ID del archivo"),
    user_id: str = Depends(get_current_user_id),
    use_case: DeleteFileUseCase = Depends(delete_file_usecase),
):
    """
    Endpoint para eliminar un archivo del vault.
    Solo el propietario (owner_id) puede eliminar el archivo.
    Protegido por JWT.
    """
    await use_case.execute(file_id, user_id)
    return DeleteResponse(
        status="success",
        message=f"Archivo {file_id} eliminado exitosamente.",
    )
