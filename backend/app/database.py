import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.base import Base

settings = get_settings()

DB_PATH = Path(os.environ.get("LOTTERY_DB_PATH", settings.db_path))
DB_DIR = DB_PATH.parent


def _engine_url(path: str | Path) -> str:
    return f"sqlite:///{Path(path).as_posix()}"


def _create_engine(path: str | Path) -> Engine:
    return create_engine(_engine_url(path), echo=False, future=True)


engine: Engine = _create_engine(DB_PATH)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def init() -> Path:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    return DB_PATH


def connect() -> Session:
    return SessionLocal()


def verify() -> None:
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
