import jwt
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.modules.users.domain.repositories.user_repository import UserRepository
from app.modules.users.exceptions.users_exceptions import (
    UserNotFoundError,
    InvalidCredentialsError,
)


class RefreshTokenUseCase:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(self, refresh_token: str) -> tuple[str, str]:
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            raise InvalidCredentialsError()
        except jwt.PyJWTError:
            raise InvalidCredentialsError()

        if payload.get("type") != "refresh":
            raise InvalidCredentialsError()

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidCredentialsError()

        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Emitir nuevo JWT Access Token
        now = datetime.now(tz=timezone.utc)
        access_payload = {
            "sub": user.id,
            "username": user.username,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        }
        new_access_token = jwt.encode(
            access_payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        # Emitir nuevo JWT Refresh Token
        refresh_payload = {
            "sub": user.id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=settings.JWT_REFRESH_EXPIRE_MINUTES),
        }
        new_refresh_token = jwt.encode(
            refresh_payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        return new_access_token, new_refresh_token
