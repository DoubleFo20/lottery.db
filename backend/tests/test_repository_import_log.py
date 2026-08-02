from app.repositories import import_log
from app.schemas.import_log import ImportLogCreate


def _payload() -> ImportLogCreate:
    return ImportLogCreate(source="test-csv", rows_imported=10, status="success")


def test_create(db_session) -> None:
    obj = import_log.create(db_session, obj_in=_payload())
    assert obj.id is not None
    assert obj.status == "success"
    assert import_log.count(db_session) == 1


def test_error_message(db_session) -> None:
    obj = import_log.create(
        db_session,
        obj_in=ImportLogCreate(
            source="test-csv", rows_imported=0, status="failed", error_message="boom"
        ),
    )
    assert obj.error_message == "boom"
