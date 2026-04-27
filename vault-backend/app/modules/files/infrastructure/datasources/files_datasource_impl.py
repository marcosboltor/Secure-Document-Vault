from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.files.domain.datasources.files_datasource import FilesDatasource
from app.modules.files.domain.entities.files import VaultFile

class FilesDatasourceImpl(FilesDatasource):
    """
    IMPLEMENTACIÓN MOCK:
    Ahora incluye el campo 'encrypted_file' con contenido binario simulado.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self._mock_files = [
            VaultFile(
                id="file-101",
                name="Contrato_Confidencialidad.pdf.vault",
                owner_id="user-001",
                owner_name="Daniel Galindo",
                recipients=["user-002"],
                created_at=datetime.utcnow(),
                signer_public_key_base64="MCowBQYDK2VwAyEAG...",
                encrypted_content=b"CONTENIDO_CIFRADO_MOCK_PDF_01" # Bytes directos
            ),
            VaultFile(
                id="file-102",
                name="Plan_Financiero_2026.xlsx.vault",
                owner_id="user-002",
                owner_name="Ana Garcia",
                recipients=["user-001"],
                created_at=datetime.utcnow(),
                signer_public_key_base64="MCowBQYDK2VwAyEB...",
                encrypted_content=b"CONTENIDO_CIFRADO_MOCK_XLSX_02"
            )
        ]

    async def get_all(self, user_id: str) -> List[VaultFile]:
        return [
            f for f in self._mock_files 
            if f.owner_id == user_id or user_id in f.recipients
        ]

    async def get_by_id(self, file_id: str) -> Optional[VaultFile]:
        return next((f for f in self._mock_files if f.id == file_id), None)

    async def save(self, file: VaultFile) -> VaultFile:
        self._mock_files.append(file)
        return file

    async def delete(self, file_id: str) -> bool:
        initial_len = len(self._mock_files)
        self._mock_files = [f for f in self._mock_files if f.id != file_id]
        return len(self._mock_files) < initial_len
