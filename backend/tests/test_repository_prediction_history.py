from datetime import date

from app.repositories import prediction_history
from app.schemas.prediction_history import PredictionHistoryCreate


def _payload(prediction_date: date) -> PredictionHistoryCreate:
    return PredictionHistoryCreate(
        prediction_date=prediction_date,
        model_name="test-model",
        predicted_numbers=["123456", "654321"],
        confidence=0.72,
    )


def test_create(db_session) -> None:
    obj = prediction_history.create(db_session, obj_in=_payload(date(2026, 1, 5)))
    assert obj.id is not None
    assert obj.predicted_numbers == ["123456", "654321"]
    assert prediction_history.count(db_session) == 1


def test_update_actual_result(db_session) -> None:
    obj = prediction_history.create(db_session, obj_in=_payload(date(2026, 1, 5)))
    from sqlalchemy.orm.attributes import flag_modified

    obj.actual_result = "123456"
    obj.accuracy = 1.0
    flag_modified(obj, "actual_result")
    flag_modified(obj, "accuracy")
    db_session.commit()
    db_session.refresh(obj)
    assert obj.actual_result == "123456"
    assert obj.accuracy == 1.0


def test_get_multi(db_session) -> None:
    prediction_history.create(db_session, obj_in=_payload(date(2026, 1, 5)))
    prediction_history.create(db_session, obj_in=_payload(date(2026, 1, 6)))
    assert prediction_history.count(db_session) == 2
