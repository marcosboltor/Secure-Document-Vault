from datetime import datetime
from typing import List
from sqlmodel import SQLModel, Field, Column, JSON
import uuid


class FileModel(SQLModel, table=True):
    __tablename__ = "files"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    owner_id: str
    owner_name: str
    recipients: List[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    signer_public_key_base64: str
    encrypted_content: bytes
