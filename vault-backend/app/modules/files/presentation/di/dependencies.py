from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.share.infrastructure.db.session import get_session
from app.modules.files.infrastructure.datasources.files_datasource_impl import FilesDatasourceImpl
from app.modules.files.infrastructure.repositories.files_repository_impl import FilesRepositoryImpl
from app.modules.files.application.use_cases.get_files_usecase import GetFilesUseCase

async def get_files_repository(session: AsyncSession = Depends(get_session)) -> FilesRepositoryImpl:
    datasource = FilesDatasourceImpl(session)
    return FilesRepositoryImpl(datasource)

async def get_files_usecase(
    repository: FilesRepositoryImpl = Depends(get_files_repository)
) -> GetFilesUseCase:
    return GetFilesUseCase(repository)
