import pytest
from datetime import date
from app.models.lottery_draw import LotteryDraw
from app.statistics.frequency_service import FrequencyService
from app.statistics.pair_frequency_service import PairFrequencyService
from app.statistics.hot_cold_service import HotColdService
from app.statistics.summary_service import SummaryService

# Create mock data
draws = [
    LotteryDraw(id=1, draw_date=date(2023, 1, 1), first_prize="123456", last_two="10"),
    LotteryDraw(id=2, draw_date=date(2023, 2, 1), first_prize="111111", last_two="10"),
    LotteryDraw(id=3, draw_date=date(2023, 3, 1), first_prize="999999", last_two="20"),
    LotteryDraw(id=4, draw_date=date(2023, 4, 1), first_prize="123123", last_two="99")
]

def test_frequency_service():
    service = FrequencyService(draws)
    fp_freq = service.get_first_prize_digit_frequency()
    # first prizes: 123456, 111111, 999999, 123123
    # '1': 1 + 6 + 0 + 2 = 9
    assert fp_freq["1"] == 9
    assert fp_freq["9"] == 6
    assert fp_freq["4"] == 1
    assert fp_freq["0"] == 0
    
    lt_freq = service.get_last_two_digit_frequency()
    # last_two: 10, 10, 20, 99
    # '1': 2
    # '0': 3
    # '2': 1
    # '9': 2
    assert lt_freq["0"] == 3
    assert lt_freq["1"] == 2
    assert lt_freq["2"] == 1
    assert lt_freq["9"] == 2
    assert lt_freq["3"] == 0

def test_pair_frequency_service():
    service = PairFrequencyService(draws)
    freq = service.get_pair_frequency()
    assert freq["10"] == 2
    assert freq["20"] == 1
    assert freq["99"] == 1
    assert freq["00"] == 0
    
    top = service.get_top_pairs(2)
    assert top[0] == ("10", 2)
    # The second one could be 20 or 99 (sorted alphabetically, so 20 is next)
    assert top[1] == ("20", 1)
    
    least = service.get_least_frequent_pairs(1)
    assert least[0][1] == 0

def test_hot_cold_service():
    service = HotColdService(draws)
    stats = service.analyze_last_two()
    
    # 10 appeared at idx 0 and 1
    assert stats["10"]["count"] == 2
    # last seen is total_draws(4) - 1 - last_idx(1) = 2
    assert stats["10"]["last_seen"] == 2
    
    # 99 appeared at idx 3
    assert stats["99"]["count"] == 1
    assert stats["99"]["last_seen"] == 0
    
    # 55 never appeared
    assert stats["55"]["count"] == 0
    assert stats["55"]["last_seen"] == 4
    assert stats["55"]["missing_streak"] == 4

    hottest = service.get_hottest(1)
    assert hottest[0] == ("10", 2)

    coldest = service.get_coldest(1)
    assert coldest[0][1] == 0

class MockDrawRepo:
    def get_all_ordered_by_date(self, db):
        return draws

def test_summary_service(monkeypatch):
    monkeypatch.setattr("app.statistics.summary_service.lottery_draw", MockDrawRepo())
    service = SummaryService(db=None) # type: ignore
    
    summary = service.get_summary()
    assert summary["total_draws"] == 4
    assert "first_prize_frequency" in summary
    assert "hottest" in summary
    assert "pair_frequency" in summary
