from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class FileResponse(BaseModel):
    id: str
    name: str
    owner_id: str
    owner_name: str
    recipients: List[str]
    created_at: datetime
    signer_public_key_base64: str

    class Config:
        from_attributes = True

class FileUploadRequest(BaseModel):
    name: str
    owner_id: str
    owner_name: str
    recipients: List[str] = []
    signer_public_key_base64: str
    # El contenido binario se maneja vía multipart/form-data, no en el JSON
