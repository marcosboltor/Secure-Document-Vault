from app.modules.files.domain.repositories.files_repository import FilesRepository
from app.modules.files.exceptions.files_exceptions import (
    FileNotFoundError,
    FileAccessDeniedError,
)


class DeleteFileUseCase:
    """
    Caso de Uso: Elimina un archivo del repositorio.
    Solo el owner_id puede eliminar el archivo.
    """

    def __init__(self, repository: FilesRepository):
        self.repository = repository

    async def execute(self, file_id: str, user_id: str) -> bool:
        file = await self.repository.get_file_details(file_id, user_id)
        if not file:
            raise FileNotFoundError(file_id=file_id)

        if not file.is_owner(user_id):
            raise FileAccessDeniedError()
        return await self.repository.remove_file(file_id, user_id)
