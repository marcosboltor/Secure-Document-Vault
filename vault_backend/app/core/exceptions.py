class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class InconsistentMetadataError(AppException):
    def __init__(self, message: str = "Metadata in DB does not match vault header"):
        super().__init__(
            code="INCONSISTENT_METADATA",
            message=message,
            status_code=400
        )

class UnauthorizedAccessError(AppException):
    def __init__(self, message: str = "You do not have access to this resource"):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=403
        )
