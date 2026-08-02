from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class LotteryDraw(TimestampMixin, Base):
    __tablename__ = "lottery_draws"

    id: Mapped[int] = mapped_column(primary_key=True)
    draw_date: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    government_round: Mapped[str | None] = mapped_column(String(50))
    first_prize: Mapped[str] = mapped_column(String(6), nullable=False)
    last_two: Mapped[str | None] = mapped_column(String(2))
    front_three: Mapped[str | None] = mapped_column(String(3))
    back_three: Mapped[str | None] = mapped_column(String(3))
    source: Mapped[str] = mapped_column(String(100), nullable=False)
