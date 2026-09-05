import csv
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.lottery_draw import LotteryDraw
from app.repositories.lottery_draw import lottery_draw
from app.schemas.lottery_draw import LotteryDrawCreate

REQUIRED_COLUMNS = {"draw_date", "first_prize", "last2"}


def _validated_number(value: str | None, *, length: int, field: str, row_number: int) -> str:
    if value is None or len(value) != length or not value.isdigit():
        raise ValueError(f"Invalid {field} at CSV row {row_number}")
    return value


def seed_history(db: Session, csv_path: Path) -> int:
    if not csv_path.is_file():
        raise FileNotFoundError(f"Lottery history dataset not found: {csv_path}")

    existing_dates = lottery_draw.get_draw_dates(db)
    new_draws: list[LotteryDraw] = []

    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            columns = set(reader.fieldnames or [])
            missing_columns = REQUIRED_COLUMNS - columns
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise ValueError(f"Lottery history dataset is missing columns: {missing}")

            for row_number, row in enumerate(reader, start=2):
                draw_date = date.fromisoformat(row["draw_date"])
                if draw_date in existing_dates:
                    continue

                first_prize = _validated_number(
                    row.get("first_prize"), length=6, field="first_prize", row_number=row_number
                )
                last_two = _validated_number(
                    row.get("last2"), length=2, field="last2", row_number=row_number
                )
                payload = LotteryDrawCreate(
                    draw_date=draw_date,
                    first_prize=first_prize,
                    last_two=last_two,
                    front_three=row.get("front3_1") or None,
                    back_three=row.get("back3_1") or None,
                    source=csv_path.name,
                )
                new_draws.append(LotteryDraw(**payload.model_dump()))
                existing_dates.add(draw_date)

        db.add_all(new_draws)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return len(new_draws)
