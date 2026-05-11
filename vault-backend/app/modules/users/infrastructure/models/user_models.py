from datetime import datetime
from typing import Optional

import uuid
from sqlmodel import SQLModel, Field


class UserModel(SQLModel, table=True):

    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str
    # Llave pública X25519 en formato PEM (para cifrado de archivos compartidos)
    public_encryption_key: str
    # Llave pública Ed25519 en formato PEM (para verificación de identidad)
    public_signing_key: str
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
