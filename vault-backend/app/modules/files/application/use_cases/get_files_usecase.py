from typing import List
from app.modules.files.domain.entities.files import VaultFile
from app.modules.files.domain.repositories.files_repository import FilesRepository


class GetFilesUseCase:
    """
    Caso de Uso: Recuperar lista de archivos.
    Encapsula la lógica de negocio para listar archivos accesibles por un usuario.
    """

    def __init__(self, repository: FilesRepository):
        self.repository = repository

    async def execute(self, user_id: str) -> List[VaultFile]:
        # TODO: Implementar de forma correcta
        files = await self.repository.get_files(user_id)
        return files
