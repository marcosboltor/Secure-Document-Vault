from typing import List
from app.modules.files.domain.entities.files import VaultFile
from app.modules.files.domain.repositories.files_repository import FilesRepository
from app.modules.files.domain.datasources.files_datasource import FilesDatasource


class FilesRepositoryImpl(FilesRepository):
    def __init__(self, datasource: FilesDatasource):
        self.datasource = datasource

    async def get_files(self, user_id: str) -> List[VaultFile]:
        return await self.datasource.get_all(user_id)

    async def get_file_details(self, file_id: str, user_id: str) -> VaultFile:
        return await self.datasource.get_by_id(file_id)

    async def upload_file(self, file: VaultFile) -> VaultFile:
        return await self.datasource.save(file)

    async def remove_file(self, file_id: str, user_id: str) -> bool:
        return await self.datasource.delete(file_id)
