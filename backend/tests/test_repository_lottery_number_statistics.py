from datetime import date

from app.repositories import lottery_number_statistics
from app.schemas.lottery_number_statistics import LotteryNumberStatisticsCreate


def _payload(number: str) -> LotteryNumberStatisticsCreate:
    return LotteryNumberStatisticsCreate(
        number=number, frequency=3, last_seen=date(2026, 1, 5), hot_score=0.8, cold_score=0.1
    )


def test_create(db_session) -> None:
    obj = lottery_number_statistics.create(db_session, obj_in=_payload("123456"))
    assert obj.id is not None
    assert obj.frequency == 3
    assert lottery_number_statistics.count(db_session) == 1


def test_unique_number(db_session) -> None:
    lottery_number_statistics.create(db_session, obj_in=_payload("123456"))
    import pytest
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        lottery_number_statistics.create(db_session, obj_in=_payload("123456"))
    db_session.rollback()


def test_get_multi(db_session) -> None:
    lottery_number_statistics.create(db_session, obj_in=_payload("111111"))
    lottery_number_statistics.create(db_session, obj_in=_payload("222222"))
    assert lottery_number_statistics.count(db_session) == 2
