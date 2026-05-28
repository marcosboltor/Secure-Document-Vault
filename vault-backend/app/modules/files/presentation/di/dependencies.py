from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.share.infrastructure.db.session import get_session
from app.modules.files.infrastructure.datasources.files_datasource_impl import (
    FilesDatasourceImpl,
)
from app.modules.files.infrastructure.repositories.files_repository_impl import (
    FilesRepositoryImpl,
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


async def get_files_repository(
    session: AsyncSession = Depends(get_session),
) -> FilesRepositoryImpl:
    datasource = FilesDatasourceImpl(session)
    return FilesRepositoryImpl(datasource)


async def get_files_usecase(
    repository: FilesRepositoryImpl = Depends(get_files_repository),
) -> GetFilesUseCase:
    return GetFilesUseCase(repository)


async def get_file_details_usecase(
    repository: FilesRepositoryImpl = Depends(get_files_repository),
) -> GetFileDetailsUseCase:
    return GetFileDetailsUseCase(repository)


async def upload_file_usecase(
    repository: FilesRepositoryImpl = Depends(get_files_repository),
) -> UploadFileUseCase:
    return UploadFileUseCase(repository)


async def delete_file_usecase(
    repository: FilesRepositoryImpl = Depends(get_files_repository),
) -> DeleteFileUseCase:
    return DeleteFileUseCase(repository)
