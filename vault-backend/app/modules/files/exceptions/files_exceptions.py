from app.modules.share.exceptions.base_exceptions import (
    DomainException,
    InfrastructureException,
)


class UserNotFoundError(DomainException):
    def __init__(self, user_id: str):
        super().__init__(
            message=f"Usuario con ID {user_id} no encontrado.",
            code="USER_NOT_FOUND",
            status_code=404,
        )


class FileNotFoundError(DomainException):
    def __init__(self, file_id: str):
        super().__init__(
            message=f"Archivo con ID {file_id} no encontrado.",
            code="FILE_NOT_FOUND",
            status_code=404,
        )


class FileAccessDeniedError(DomainException):
    def __init__(self):
        super().__init__(
            message="No tienes permiso para acceder a este archivo.",
            code="FILE_ACCESS_DENIED",
            status_code=403,
        )


class FileStorageError(InfrastructureException):
    def __init__(self, detail: str):
        super().__init__(
            message=f"Error en el almacenamiento de archivos: {detail}",
            code="FILE_STORAGE_ERROR",
        )
