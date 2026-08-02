from typing import List, Dict, Tuple
from collections import Counter
from app.models.lottery_draw import LotteryDraw

class PairFrequencyService:
    def __init__(self, draws: List[LotteryDraw]):
        self.draws = draws

    def get_pair_frequency(self) -> Dict[str, int]:
        """Calculates the frequency of every pair (00-99) in last_two."""
        counter = Counter()
        for draw in self.draws:
            if draw.last_two and len(draw.last_two) == 2:
                counter.update([draw.last_two])
                
        # Ensure all 00-99 are present
        result = {}
        for i in range(100):
            pair = f"{i:02d}"
            result[pair] = counter.get(pair, 0)
        return result

    def get_top_pairs(self, n: int = 5) -> List[Tuple[str, int]]:
        """Returns the top N most frequent pairs."""
        freq = self.get_pair_frequency()
        # Sort by frequency descending, then by pair string ascending to be deterministic
        sorted_pairs = sorted(freq.items(), key=lambda item: (-item[1], item[0]))
        return sorted_pairs[:n]

    def get_least_frequent_pairs(self, n: int = 5) -> List[Tuple[str, int]]:
        """Returns the least frequent pairs."""
        freq = self.get_pair_frequency()
        # Sort by frequency ascending, then by pair string ascending to be deterministic
        sorted_pairs = sorted(freq.items(), key=lambda item: (item[1], item[0]))
        return sorted_pairs[:n]
