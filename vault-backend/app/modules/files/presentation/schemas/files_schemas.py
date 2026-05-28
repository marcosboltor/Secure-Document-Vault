from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class FileListResponse(BaseModel):
    """Respuesta para listado de archivos (sin contenido cifrado)."""

    id: str
    name: str
    owner_id: str
    owner_name: str
    recipients: List[str]
    created_at: datetime
    signer_public_key_base64: str
    size: int = 0

    class Config:
        from_attributes = True


class FileDetailResponse(BaseModel):
    """Respuesta con detalles completos del archivo (incluye contenido cifrado)."""

    id: str
    name: str
    owner_id: str
    owner_name: str
    recipients: List[str]
    created_at: datetime
    signer_public_key_base64: str
    size: int = 0
    encrypted_content: Optional[str] = None

    class Config:
        from_attributes = True


# Alias para compatibilidad con imports existentes
FileResponse = FileListResponse


class FileUploadRequest(BaseModel):
    """Esquema para la solicitud de subida de archivo."""

    name: str
    recipients: List[str] = []
    encrypted_content: str  # Contenido cifrado codificado en base64


class DeleteResponse(BaseModel):
    """Respuesta para la eliminación de un archivo."""

    status: str = "success"
    message: str
