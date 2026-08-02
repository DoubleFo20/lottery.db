from typing import List, Dict
from collections import Counter
from app.models.lottery_draw import LotteryDraw

class FrequencyService:
    def __init__(self, draws: List[LotteryDraw]):
        self.draws = draws

    def get_overall_digit_frequency(self) -> Dict[str, int]:
        """Calculates the frequency of every digit (0-9) across first_prize and last_two."""
        counter = Counter()
        for draw in self.draws:
            if draw.first_prize:
                counter.update(list(draw.first_prize))
            if draw.last_two:
                counter.update(list(draw.last_two))
                
        return self._format_counter(counter)

    def get_first_prize_digit_frequency(self) -> Dict[str, int]:
        """Calculates the frequency of every digit (0-9) in first_prize only."""
        counter = Counter()
        for draw in self.draws:
            if draw.first_prize:
                counter.update(list(draw.first_prize))
                
        return self._format_counter(counter)

    def get_last_two_digit_frequency(self) -> Dict[str, int]:
        """Calculates the frequency of every digit (0-9) in last_two only."""
        counter = Counter()
        for draw in self.draws:
            if draw.last_two:
                counter.update(list(draw.last_two))
                
        return self._format_counter(counter)
        
    def _format_counter(self, counter: Counter) -> Dict[str, int]:
        # Ensure all digits 0-9 are present in the result even if count is 0
        result = {}
        for i in range(10):
            digit = str(i)
            result[digit] = counter.get(digit, 0)
        return result
