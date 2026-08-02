from datetime import date, datetime

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class LotteryDrawBase(BaseSchema):
    draw_date: date
    government_round: str | None = None
    first_prize: str
    last_two: str | None = None
    front_three: str | None = None
    back_three: str | None = None
    source: str


class LotteryDrawCreate(LotteryDrawBase):
    pass


class LotteryDrawRead(LotteryDrawBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
