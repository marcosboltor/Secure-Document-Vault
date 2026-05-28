from abc import ABC, abstractmethod
from typing import List
from app.modules.files.domain.entities.files import VaultFile


class FilesRepository(ABC):
    @abstractmethod
    async def get_files(self, user_id: str) -> List[VaultFile]:
        """Recupera la lista de archivos para un usuario específico."""
        pass

    @abstractmethod
    async def get_file_details(self, file_id: str, user_id: str) -> VaultFile:
        """Recupera los detalles de un archivo si el usuario tiene acceso."""
        pass

    @abstractmethod
    async def upload_file(self, file: VaultFile) -> VaultFile:
        """Carga un nuevo archivo al vault."""
        pass

    @abstractmethod
    async def remove_file(self, file_id: str, user_id: str) -> bool:
        """Elimina un archivo si el usuario es el propietario."""
        pass
