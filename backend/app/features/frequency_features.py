from typing import List

class FrequencyFeatures:
    @staticmethod
    def get_digit_frequency(history_values: List[str], num: str) -> int:
        """Counts how many times 'num' appears exactly in the history."""
        if not history_values or not num: return 0
        return history_values.count(num)

    @staticmethod
    def get_rolling_frequency(history_values: List[str], num: str, window: int) -> int:
        """Counts how many times 'num' appears in the last 'window' draws."""
        if not history_values or not num or window <= 0: return 0
        recent = history_values[-window:]
        return recent.count(num)

    @staticmethod
    def get_moving_average(history_values: List[str], num: str, window: int) -> float:
        """Returns the probability of 'num' appearing in the last 'window' draws."""
        if not history_values or not num or window <= 0: return 0.0
        recent = history_values[-window:]
        if not recent: return 0.0
        return recent.count(num) / len(recent)

    @staticmethod
    def get_normalized_frequency(history_values: List[str], num: str) -> float:
        """Returns the probability of 'num' appearing over the entire history."""
        if not history_values or not num: return 0.0
        return history_values.count(num) / len(history_values)
