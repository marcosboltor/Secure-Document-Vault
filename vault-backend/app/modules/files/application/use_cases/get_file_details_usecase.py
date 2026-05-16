from app.modules.files.domain.entities.files import VaultFile
from app.modules.files.domain.repositories.files_repository import FilesRepository
from app.modules.files.exceptions.files_exceptions import (
    FileNotFoundError,
    FileAccessDeniedError,
)


class GetFileDetailsUseCase:
    """
    Caso de Uso: Recuperar archivo por ID.
    Encapsula la lógica de negocio obtener un archivo por su ID
    verificando si el usuario cuenta con permisos para acceder a el.
    """

    def __init__(self, repository: FilesRepository):
        self.repository = repository

    async def execute(self, file_id: str, user_id: str) -> VaultFile:
        file = await self.repository.get_file_details(file_id, user_id)
        if not file:
            raise FileNotFoundError(file_id)

        if not file.has_access(user_id):
            raise FileAccessDeniedError()
        return file
