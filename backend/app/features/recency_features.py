from typing import List

class RecencyFeatures:
    @staticmethod
    def get_recent_occurrence(history_values: List[str], num: str, window: int) -> int:
        """Returns the number of times 'num' appeared in the last 'window' draws. (Same as rolling_frequency)"""
        if not history_values or not num or window <= 0: return 0
        return history_values[-window:].count(num)

    @staticmethod
    def get_weighted_recency(history_values: List[str], num: str) -> float:
        """
        Calculates a linear weighted sum where more recent occurrences have higher weight.
        Weight = position_index + 1
        Returns normalized weight sum.
        """
        if not history_values or not num: return 0.0
        
        n = len(history_values)
        # Sum of all possible weights is n(n+1)/2
        max_possible_weight = (n * (n + 1)) / 2
        if max_possible_weight == 0: return 0.0
        
        weight_sum = 0
        for i, val in enumerate(history_values):
            if val == num:
                weight_sum += (i + 1)
                
        return weight_sum / max_possible_weight

    @staticmethod
    def get_exponential_decay(history_values: List[str], num: str, alpha: float = 0.5) -> float:
        """
        Calculates exponentially weighted occurrences.
        Weight for gap k = (1-alpha)^k. k=0 for the most recent draw.
        """
        if not history_values or not num: return 0.0
        
        score = 0.0
        # Iterate backwards
        for k, val in enumerate(reversed(history_values)):
            if val == num:
                score += (1 - alpha) ** k
                
        return score
