import base64
from datetime import datetime, timezone, timedelta

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature

from app.core.config import settings
from app.modules.users.domain.repositories.user_repository import UserRepository
from app.modules.users.exceptions.users_exceptions import (
    UserNotFoundError,
    InvalidCredentialsError,
)


class LoginUseCase:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(self, user_id: str, challenge: str, signature_b64: str) -> tuple[str, str]:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Cargar la llave pública Ed25519 desde PEM
        try:
            public_key = load_pem_public_key(user.public_signing_key.encode())
            if not isinstance(public_key, Ed25519PublicKey):
                raise InvalidCredentialsError()
        except Exception:
            raise InvalidCredentialsError()

        # Verificar la firma Ed25519
        try:
            signature_bytes = base64.b64decode(signature_b64)
            public_key.verify(signature_bytes, challenge.encode())
        except (InvalidSignature, Exception):
            raise InvalidCredentialsError()

        # Emitir JWT Access Token
        now = datetime.now(tz=timezone.utc)
        access_payload = {
            "sub": user.id,
            "username": user.username,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        }
        access_token = jwt.encode(
            access_payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        # Emitir JWT Refresh Token
        refresh_payload = {
            "sub": user.id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=settings.JWT_REFRESH_EXPIRE_MINUTES),
        }
        refresh_token = jwt.encode(
            refresh_payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        return access_token, refresh_token
