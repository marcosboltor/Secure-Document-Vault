import uuid
from datetime import datetime
from app.modules.files.domain.entities.files import VaultFile
from app.modules.files.domain.repositories.files_repository import FilesRepository


class UploadFileUseCase:
    """
    Caso de Uso: Subir un archivo al vault.
    Recibe la entidad VaultFile ya construida y la persiste a través del repositorio.
    """

    def __init__(self, repository: FilesRepository):
        self.repository = repository

    async def execute(self, metadata: dict, binary_blob: bytes) -> VaultFile:
        file_id = str(uuid.uuid4())
        file = VaultFile(
            id=file_id,
            name=metadata.get("name"),
            owner_id=metadata.get("owner_id"),
            owner_name=metadata.get("owner_name"),
            recipients=metadata.get("recipients", []),
            created_at=datetime.utcnow(),
            signer_public_key_base64=metadata.get("signer_public_key_base64"),
            encrypted_content=binary_blob,
        )
        # TODO: Implementar una vez resuelto Issue 2
        # Verificar que existe el usuario con el owner_id en el repositorio de Usuarios
        saved_file = await self.repository.upload_file(file)
        return saved_file
