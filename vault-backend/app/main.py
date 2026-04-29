from app.core.logger import setup_logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.router import router
from app.api.middlewares.cors import setup_cors
from app.core.config import settings
from app.core.exceptions.global_handlers import setup_exception_handlers

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

setup_cors(app)
setup_exception_handlers(app)

app.include_router(router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok"}
