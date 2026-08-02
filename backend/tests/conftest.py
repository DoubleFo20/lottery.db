import pytest
from sqlalchemy.orm import Session, sessionmaker

from app import database
from app.models.base import Base


@pytest.fixture()
def db_session(tmp_path, monkeypatch) -> Session:
    test_path = tmp_path / "test.sqlite"
    engine = database._create_engine(test_path)
    monkeypatch.setattr(database, "DB_PATH", test_path)
    monkeypatch.setattr(database, "DB_DIR", tmp_path)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(
        database,
        "SessionLocal",
        sessionmaker(bind=engine, class_=Session, autoflush=False, expire_on_commit=False),
    )
    Base.metadata.create_all(bind=engine)
    with database.SessionLocal() as session:
        yield session
