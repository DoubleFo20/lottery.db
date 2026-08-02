from datetime import date

from app.repositories import lottery_draw
from app.schemas.lottery_draw import LotteryDrawCreate


def _payload(draw_date: date, first_prize: str) -> LotteryDrawCreate:
    return LotteryDrawCreate(
        draw_date=draw_date,
        government_round="G-2026-01",
        first_prize=first_prize,
        last_two=first_prize[-2:],
        front_three=first_prize[:3],
        back_three=first_prize[-3:],
        source="test-csv",
    )


def test_create(db_session) -> None:
    obj = lottery_draw.create(db_session, obj_in=_payload(date(2026, 1, 5), "123456"))
    assert obj.id is not None
    assert obj.first_prize == "123456"
    assert lottery_draw.count(db_session) == 1


def test_get_and_get_multi(db_session) -> None:
    a = lottery_draw.create(db_session, obj_in=_payload(date(2026, 1, 5), "111111"))
    b = lottery_draw.create(db_session, obj_in=_payload(date(2026, 1, 6), "222222"))
    assert lottery_draw.get(db_session, a.id).id == a.id
    ids = {o.id for o in lottery_draw.get_multi(db_session)}
    assert ids == {a.id, b.id}


def test_unique_draw_date(db_session) -> None:
    lottery_draw.create(db_session, obj_in=_payload(date(2026, 1, 5), "111111"))
    import pytest
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        lottery_draw.create(db_session, obj_in=_payload(date(2026, 1, 5), "222222"))
    db_session.rollback()


def test_get_by_draw_date(db_session) -> None:
    lottery_draw.create(db_session, obj_in=_payload(date(2026, 1, 5), "111111"))
    found = lottery_draw.get_by_draw_date(db_session, date(2026, 1, 5))
    assert found is not None
    assert found.first_prize == "111111"


def test_remove(db_session) -> None:
    obj = lottery_draw.create(db_session, obj_in=_payload(date(2026, 1, 5), "111111"))
    removed = lottery_draw.remove(db_session, id=obj.id)
    assert removed is not None
    assert lottery_draw.get(db_session, obj.id) is None
