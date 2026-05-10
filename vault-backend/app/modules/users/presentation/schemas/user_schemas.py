from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    # Llave pública X25519 en formato PEM — generada en el cliente
    public_encryption_key: str
    # Llave pública Ed25519 en formato PEM — generada en el cliente
    public_signing_key: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre de usuario no puede estar vacío.")
        return v.strip()


class LoginRequest(BaseModel):
    user_id: str
    # Texto que el cliente firmó con su llave privada Ed25519
    challenge: str
    # Firma en base64 producida por la llave privada Ed25519 del cliente
    signature: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutResponse(BaseModel):
    message: str


class UserPublicResponse(BaseModel):
    id: str
    username: str
    # Solo la llave de cifrado X25519 se expone para selección de destinatarios
    public_encryption_key: str
    created_at: datetime
