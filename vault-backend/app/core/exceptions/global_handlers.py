import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
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
