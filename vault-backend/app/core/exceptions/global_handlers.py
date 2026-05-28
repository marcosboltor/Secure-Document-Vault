import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.modules.share.exceptions.base_exceptions import AppBaseException

# Usamos el logger configurado globalmente
logger = logging.getLogger("app")


def setup_exception_handlers(app: FastAPI):

    @app.exception_handler(AppBaseException)
    async def app_exception_handler(request: Request, exc: AppBaseException):
        """
        Manejador para excepciones controladas de la aplicación
        (Dominio e Infraestructura).
        """
        logger.warning(
            f"AppException [{exc.code}]: {exc.message} at {request.url.path}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "error", "code": exc.code, "message": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Manejador para errores de validación de Pydantic (Capa de Presentación)."""
        logger.warning(f"Validation Error at {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "code": "VALIDATION_ERROR",
                "message": "Los datos enviados no son validos.",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """
        Manejador para errores de integridad de base de datos
        (violaciones de constraint, duplicados, FK inválidas).
        """
        logger.error(
            f"Database IntegrityError at {request.url.path}: {str(exc)}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "status": "error",
                "code": "DATABASE_INTEGRITY_ERROR",
                "message": "Conflicto de integridad en la base de datos. "
                "El recurso ya existe o viola una restricción.",
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        """
        Manejador para errores genéricos de base de datos
        (conexión fallida, pool agotado, errores operacionales).
        """
        logger.error(
            f"Database SQLAlchemyError at {request.url.path}: {str(exc)}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "status": "error",
                "code": "DATABASE_CONNECTION_ERROR",
                "message": "Error de comunicación con la base de datos. "
                "Intente de nuevo más tarde.",
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Manejador para errores no controlados (500)."""
        logger.error(
            f"Unhandled Exception at {request.url.path}: {str(exc)}", exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Ocurrio un error inesperado en el servidor.",
            },
        )
