from datetime import date, datetime

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class PredictionHistoryBase(BaseSchema):
    prediction_date: date
    model_name: str
    predicted_numbers: list[str]
    confidence: float = 0.0
    actual_result: str | None = None
    accuracy: float | None = None


class PredictionHistoryCreate(PredictionHistoryBase):
    pass


class PredictionHistoryRead(PredictionHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
