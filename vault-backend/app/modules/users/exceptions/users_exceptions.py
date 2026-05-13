from app.modules.share.exceptions.base_exceptions import DomainException


class UserAlreadyExistsError(DomainException):
    def __init__(self, email: str):
        super().__init__(
            message=f"El email '{email}' ya está registrado.",
            code="USER_ALREADY_EXISTS",
            status_code=409,
        )


class InvalidCredentialsError(DomainException):
    def __init__(self):
        super().__init__(
            message="La firma proporcionada no es válida.",
            code="INVALID_CREDENTIALS",
            status_code=401,
        )


class UserNotFoundError(DomainException):
    def __init__(self, identifier: str):
        super().__init__(
            message=f"Usuario '{identifier}' no encontrado.",
            code="USER_NOT_FOUND",
            status_code=404,
        )
