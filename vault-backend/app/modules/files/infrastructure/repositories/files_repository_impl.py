from typing import List, Optional
from app.modules.files.domain.entities.files import VaultFile
from app.modules.files.domain.repositories.files_repository import FilesRepository
from app.modules.files.domain.datasources.files_datasource import FilesDatasource
from app.modules.files.exceptions.files_exceptions import FileNotFoundError, FileAccessDeniedError

class FilesRepositoryImpl(FilesRepository):
    def __init__(self, datasource: FilesDatasource):
        self.datasource = datasource

    async def get_files(self, user_id: str) -> List[VaultFile]:
        return await self.datasource.get_all(user_id)

    async def get_file_details(self, file_id: str, user_id: str) -> VaultFile:
        file = await self.datasource.get_by_id(file_id)
        if not file:
            raise FileNotFoundError(file_id)
        
        if not file.has_access(user_id):
            raise FileAccessDeniedError()
            
        return file

    async def upload_file(self, file: VaultFile) -> VaultFile:
        return await self.datasource.save(file)

    async def remove_file(self, file_id: str, user_id: str) -> bool:
        file = await self.datasource.get_by_id(file_id)
        if not file:
            raise FileNotFoundError(file_id)
            
        if not file.is_owner(user_id):
            raise FileAccessDeniedError()
            
        return await self.datasource.delete(file_id)
