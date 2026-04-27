import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.share.exceptions.base_exceptions import AppBaseException

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI):

    @app.exception_handler(AppBaseException)
    async def app_exception_handler(request: Request, exc: AppBaseException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "error", "code": exc.code, "message": exc.message},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Ocurrió un error inesperado en el servidor.",
            },
        )
