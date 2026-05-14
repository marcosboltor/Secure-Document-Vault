import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, or_, cast
from sqlalchemy.dialects.postgresql import JSONB
from app.modules.files.domain.datasources.files_datasource import FilesDatasource
from app.modules.files.domain.entities.files import VaultFile
from app.modules.files.infrastructure.models.files_models import FileModel
from app.modules.files.exceptions.files_exceptions import (
    FileNotFoundError,
    FileStorageError,
)

logger = logging.getLogger("app")


class FilesDatasourceImpl(FilesDatasource):
    """
    Implementación del datasource de archivos con PostgreSQL.
    Maneja la persistencia y recuperación de archivos cifrados.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    def _map_to_domain(self, file: FileModel) -> VaultFile:
        return VaultFile(
            id=file.id,
            name=file.name,
            owner_id=file.owner_id,
            owner_name=file.owner_name,
            recipients=file.recipients or [],
            created_at=file.created_at,
            signer_public_key_base64=file.signer_public_key_base64,
            encrypted_content=file.encrypted_content,
        )

    def _map_to_model(self, file: VaultFile) -> FileModel:
        return FileModel(
            id=file.id,
            name=file.name,
            owner_id=file.owner_id,
            owner_name=file.owner_name,
            recipients=file.recipients or [],
            created_at=file.created_at,
            signer_public_key_base64=file.signer_public_key_base64,
            encrypted_content=file.encrypted_content,
        )

    async def get_all(self, user_id: str) -> List[VaultFile]:
        try:
            query = select(FileModel).where(
                or_(
                    FileModel.owner_id == user_id,
                    cast(FileModel.recipients, JSONB).op("@>")(cast(f'["{user_id}"]', JSONB)),
                )
            )
            result = await self.session.execute(query)
            files = result.scalars().all()
            return [self._map_to_domain(f) for f in files]
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener archivos para usuario {user_id}: {e}")
            raise FileStorageError(f"Error al obtener la lista de archivos: {str(e)}")

    async def get_by_id(self, file_id: str) -> Optional[VaultFile]:
        try:
            query = select(FileModel).where(FileModel.id == file_id)
            result = await self.session.execute(query)
            file = result.scalar_one_or_none()
            if not file:
                raise FileNotFoundError(file_id)
            return self._map_to_domain(file)
        except FileNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener archivo {file_id}: {e}")
            raise FileStorageError(f"Error al obtener el archivo: {str(e)}")

    async def save(self, file: VaultFile) -> VaultFile:
        try:
            db_file = self._map_to_model(file)
            self.session.add(db_file)
            await self.session.commit()
            await self.session.refresh(db_file)
            return self._map_to_domain(db_file)
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error al guardar archivo {file.name}: {e}")
            raise FileStorageError(
                f"Conflicto de integridad al guardar el archivo: {str(e)}"
            )
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error al guardar archivo {file.name}: {e}")
            raise FileStorageError(f"Error al guardar el archivo: {str(e)}")

    async def delete(self, file_id: str) -> bool:
        try:
            query = select(FileModel).where(FileModel.id == file_id)
            result = await self.session.execute(query)
            db_file = result.scalar_one_or_none()
            if not db_file:
                raise FileNotFoundError(file_id)
            await self.session.delete(db_file)
            await self.session.commit()
            return True
        except FileNotFoundError:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error al eliminar archivo {file_id}: {e}")
            raise FileStorageError(f"Error al eliminar el archivo: {str(e)}")
