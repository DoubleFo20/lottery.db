from datetime import date

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class LotteryNumberStatisticsBase(BaseSchema):
    number: str
    frequency: int = 0
    last_seen: date | None = None
    hot_score: float = 0.0
    cold_score: float = 0.0


class LotteryNumberStatisticsCreate(LotteryNumberStatisticsBase):
    pass


class LotteryNumberStatisticsRead(LotteryNumberStatisticsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
