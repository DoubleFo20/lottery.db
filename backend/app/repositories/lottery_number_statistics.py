from app.models.lottery_number_statistics import LotteryNumberStatistics
from app.repositories.base import CRUDBase
from app.schemas.lottery_number_statistics import LotteryNumberStatisticsCreate


class LotteryNumberStatisticsRepository(
    CRUDBase[LotteryNumberStatistics, LotteryNumberStatisticsCreate]
):
    pass


lottery_number_statistics = LotteryNumberStatisticsRepository(LotteryNumberStatistics)
