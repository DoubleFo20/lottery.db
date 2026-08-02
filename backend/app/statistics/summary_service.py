from sqlalchemy.orm import Session
from typing import Dict, Any
from app.repositories.lottery_draw import lottery_draw
from app.statistics.frequency_service import FrequencyService
from app.statistics.pair_frequency_service import PairFrequencyService
from app.statistics.hot_cold_service import HotColdService

class SummaryService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self) -> Dict[str, Any]:
        """
        Retrieves all draws and compiles a complete statistical summary.
        """
        draws = lottery_draw.get_all_ordered_by_date(self.db)
        
        freq_service = FrequencyService(draws)
        pair_freq_service = PairFrequencyService(draws)
        hot_cold_service = HotColdService(draws)
        
        return {
            "total_draws": len(draws),
            "first_prize_frequency": freq_service.get_first_prize_digit_frequency(),
            "last_two_frequency": freq_service.get_last_two_digit_frequency(),
            "overall_digit_frequency": freq_service.get_overall_digit_frequency(),
            "hottest": [dict(number=num, count=count) for num, count in hot_cold_service.get_hottest(5)],
            "coldest": [dict(number=num, count=count) for num, count in hot_cold_service.get_coldest(5)],
            "pair_frequency": pair_freq_service.get_pair_frequency(),
            "hot_cold_details": hot_cold_service.analyze_last_two()
        }
