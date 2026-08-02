from datetime import date

from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LotteryNumberStatistics(Base):
    __tablename__ = "lottery_number_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(6), unique=True, index=True, nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_seen: Mapped[date | None] = mapped_column(Date)
    hot_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cold_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
