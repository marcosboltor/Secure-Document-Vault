from abc import ABC, abstractmethod
from typing import List, Optional
from app.modules.files.domain.entities.files import VaultFile


class FilesDatasource(ABC):
    @abstractmethod
    async def get_all(self, user_id: str) -> List[VaultFile]:
        """Obtiene todos los archivos accesibles por un usuario."""
        pass

    @abstractmethod
    async def get_by_id(self, file_id: str) -> Optional[VaultFile]:
        """Obtiene un archivo por su ID."""
        pass

    @abstractmethod
    async def save(self, file: VaultFile) -> VaultFile:
        """Guarda un nuevo archivo o actualiza uno existente."""
        pass

    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """Elimina un archivo por su ID."""
        pass
