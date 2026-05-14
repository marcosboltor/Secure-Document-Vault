import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.share.infrastructure.db.session import get_session
from app.modules.users.infrastructure.datasources.user_datasource_impl import (
    UserDatasourceImpl,
)
from app.modules.users.infrastructure.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from app.modules.users.application.use_cases.register_user_usecase import (
    RegisterUserUseCase,
)
from app.modules.users.application.use_cases.login_usecase import LoginUseCase
from app.modules.users.application.use_cases.list_users_usecase import (
    ListUsersUseCase,
)
from app.modules.users.application.use_cases.refresh_token_usecase import (
    RefreshTokenUseCase,
)

_bearer_scheme = HTTPBearer()


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepositoryImpl:
    datasource = UserDatasourceImpl(session)
    return UserRepositoryImpl(datasource)


async def get_register_usecase(
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(repository)


async def get_login_usecase(
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> LoginUseCase:
    return LoginUseCase(repository)


async def get_list_users_usecase(
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> ListUsersUseCase:
    return ListUsersUseCase(repository)


async def get_refresh_token_usecase(
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(repository)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        token_type = payload.get("type")
        if token_type and token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: se esperaba un access token.",
            )

        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: falta el campo 'sub'.",
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        )


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    repository: UserRepositoryImpl = Depends(get_user_repository)
):
    user = await repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario autenticado ya no existe.",
        )
    return user
