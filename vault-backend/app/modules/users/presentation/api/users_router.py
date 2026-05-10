from typing import List

from fastapi import APIRouter, Depends, status

from app.modules.users.application.use_cases.register_user_usecase import RegisterUserUseCase
from app.modules.users.application.use_cases.login_usecase import LoginUseCase
from app.modules.users.application.use_cases.list_users_usecase import ListUsersUseCase
from app.modules.users.application.use_cases.refresh_token_usecase import RefreshTokenUseCase
from app.modules.users.presentation.di.dependencies import (
    get_register_usecase,
    get_login_usecase,
    get_list_users_usecase,
    get_refresh_token_usecase,
    get_current_user_id,
)
from app.modules.users.presentation.schemas.user_schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserPublicResponse,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserPublicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description=(
        "Crea una nueva identidad en el sistema. El cliente genera sus llaves "
        "criptográficas (X25519 para cifrado, Ed25519 para firma) y sólo envía "
        "las **llaves públicas** — el servidor nunca conoce la llave privada."
    ),
)
async def register(
    body: RegisterRequest,
    use_case: RegisterUserUseCase = Depends(get_register_usecase),
) -> UserPublicResponse:
    user = await use_case.execute(
        email=body.email,
        username=body.username,
        public_encryption_key=body.public_encryption_key,
        public_signing_key=body.public_signing_key,
    )
    return UserPublicResponse(
        id=user.id,
        username=user.username,
        public_encryption_key=user.public_encryption_key,
        created_at=user.created_at,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión (Zero-Knowledge)",
    description=(
        "Autentica al usuario mediante **firma criptográfica Ed25519**. "
        "El cliente firma un `challenge` con su llave privada y el servidor "
        "verifica la firma contra la llave pública registrada. "
        "Si es válida, emite un JWT de acceso."
    ),
)
async def login(
    body: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_usecase),
) -> TokenResponse:
    access_token, refresh_token = await use_case.execute(
        user_id=body.user_id,
        challenge=body.challenge,
        signature_b64=body.signature,
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Renovar token de acceso",
    description=(
        "Recibe un `refresh_token` válido y emite un nuevo par de tokens "
        "(`access_token` y `refresh_token`). Esto permite mantener la sesión "
        "activa sin que el cliente tenga que volver a firmar criptográficamente."
    ),
)
async def refresh_token(
    body: RefreshTokenRequest,
    use_case: RefreshTokenUseCase = Depends(get_refresh_token_usecase),
) -> TokenResponse:
    new_access_token, new_refresh_token = await use_case.execute(
        refresh_token=body.refresh_token,
    )
    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)

@router.get(
    "/",
    response_model=List[UserPublicResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar usuarios",
    description=(
        "Devuelve la lista de todos los usuarios registrados con sus datos públicos. "
        "Requiere autenticación mediante JWT. Útil para seleccionar destinatarios "
        "al compartir un documento cifrado."
    ),
)
async def list_users(
    _current_user_id: str = Depends(get_current_user_id),
    use_case: ListUsersUseCase = Depends(get_list_users_usecase),
) -> List[UserPublicResponse]:
    users = await use_case.execute()
    return [
        UserPublicResponse(
            id=u.id,
            username=u.username,
            public_encryption_key=u.public_encryption_key,
            created_at=u.created_at,
        )
        for u in users
    ]
