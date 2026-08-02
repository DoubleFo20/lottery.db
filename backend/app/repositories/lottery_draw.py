from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lottery_draw import LotteryDraw
from app.repositories.base import CRUDBase
from app.schemas.lottery_draw import LotteryDrawCreate


class LotteryDrawRepository(CRUDBase[LotteryDraw, LotteryDrawCreate]):
    def get_by_draw_date(self, db: Session, draw_date: object) -> LotteryDraw | None:
        return db.scalar(select(LotteryDraw).where(LotteryDraw.draw_date == draw_date))
        
    def get_all_ordered_by_date(self, db: Session) -> list[LotteryDraw]:
        return list(db.scalars(select(LotteryDraw).order_by(LotteryDraw.draw_date.asc())))

lottery_draw = LotteryDrawRepository(LotteryDraw)
