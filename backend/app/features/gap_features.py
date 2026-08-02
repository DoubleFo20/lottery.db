from typing import List

class GapFeatures:
    @staticmethod
    def get_gap_since_last(history_values: List[str], num: str) -> int:
        """Returns the number of draws since 'num' last appeared. If never, returns len(history)."""
        if not history_values or not num: return 0
        try:
            # Reverse history to find the most recent appearance (end of list is most recent)
            # e.g., if it's the very last item, gap is 0
            idx = history_values[::-1].index(num)
            return idx
        except ValueError:
            return len(history_values)

    @staticmethod
    def get_average_gap(history_values: List[str], num: str) -> float:
        """Returns the average gap between appearances of 'num'."""
        if not history_values or not num: return 0.0
        
        indices = [i for i, val in enumerate(history_values) if val == num]
        if len(indices) < 2:
            return 0.0
            
        gaps = [indices[i] - indices[i-1] - 1 for i in range(1, len(indices))]
        return sum(gaps) / len(gaps)

    @staticmethod
    def get_max_gap(history_values: List[str], num: str) -> int:
        """Returns the maximum gap between appearances of 'num'."""
        if not history_values or not num: return 0
        
        indices = [i for i, val in enumerate(history_values) if val == num]
        if not indices:
            return len(history_values)
            
        gaps = [indices[i] - indices[i-1] - 1 for i in range(1, len(indices))]
        
        # Also consider the gap from start to first appearance, and last appearance to end
        gaps.append(indices[0])
        gaps.append(len(history_values) - 1 - indices[-1])
        
        return max(gaps)

    @staticmethod
    def get_current_missing_streak(history_values: List[str], num: str) -> int:
        """Alias for get_gap_since_last, representing the ongoing gap."""
        return GapFeatures.get_gap_since_last(history_values, num)
