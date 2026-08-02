from datetime import date

from sqlalchemy import JSON, Date, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PredictionHistory(TimestampMixin, Base):
    __tablename__ = "prediction_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    predicted_numbers: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    actual_result: Mapped[str | None] = mapped_column(String(6))
    accuracy: Mapped[float | None] = mapped_column(Float)
