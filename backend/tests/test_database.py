from sqlalchemy.orm import Session, sessionmaker

from app import database


def test_init_creates_database_file(tmp_path, monkeypatch) -> None:
    test_path = tmp_path / "lottery.sqlite"
    engine = database._create_engine(test_path)
    monkeypatch.setattr(database, "DB_PATH", test_path)
    monkeypatch.setattr(database, "DB_DIR", tmp_path)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(
        database,
        "SessionLocal",
        sessionmaker(bind=engine, class_=Session, autoflush=False, expire_on_commit=False),
    )
    path = database.init()
    assert path == test_path
    assert path.exists()
    database.verify()
