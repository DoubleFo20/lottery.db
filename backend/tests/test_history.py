from datetime import date

from fastapi.testclient import TestClient

from app import database
from app.main import app
from app.models.lottery_draw import LotteryDraw
from app.services.history_seed_service import seed_history


def _write_history_csv(path) -> None:
    path.write_text(
        "draw_date,first_prize,front3_1,back3_1,last2\n"
        "2026-07-01,751495,001,304,62\n"
        "2026-06-16,287184,758,007,48\n",
        encoding="utf-8",
    )


def test_seed_history_is_idempotent(db_session, tmp_path) -> None:
    csv_path = tmp_path / "lottery_history.csv"
    _write_history_csv(csv_path)

    assert seed_history(db_session, csv_path) == 2
    assert seed_history(db_session, csv_path) == 0

    draws = db_session.query(LotteryDraw).order_by(LotteryDraw.draw_date.desc()).all()
    assert [(draw.draw_date, draw.first_prize, draw.last_two) for draw in draws] == [
        (date(2026, 7, 1), "751495", "62"),
        (date(2026, 6, 16), "287184", "48"),
    ]


def test_history_returns_newest_first(db_session) -> None:
    db_session.add_all(
        [
            LotteryDraw(
                draw_date=date(2026, 6, 16),
                first_prize="287184",
                last_two="48",
                source="test",
            ),
            LotteryDraw(
                draw_date=date(2026, 7, 1),
                first_prize="751495",
                last_two="62",
                source="test",
            ),
        ]
    )
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[database.get_db] = override_get_db
    try:
        client = TestClient(app)
        response = client.get("/history", params={"offset": 0, "limit": 1})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["total"] == 2
    assert payload["data"]["items"] == [
        {
            "id": payload["data"]["items"][0]["id"],
            "draw_date": "2026-07-01",
            "first_prize": "751495",
            "last_two": "62",
        }
    ]


def test_history_rejects_invalid_limit(db_session) -> None:
    def override_get_db():
        yield db_session

    app.dependency_overrides[database.get_db] = override_get_db
    try:
        client = TestClient(app)
        response = client.get("/history", params={"limit": 0})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
