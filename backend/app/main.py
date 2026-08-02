from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import database
from app.constants import HEALTH_PATH, STATUS_OK
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.exceptions import register_exception_handlers

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    database.init()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get(HEALTH_PATH)
def health() -> dict[str, str]:
    database.verify()
    return {"status": STATUS_OK}
