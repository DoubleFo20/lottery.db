from typing import List, Dict, Any
from app.features.digit_features import DigitFeatures
from app.features.pattern_features import PatternFeatures
from app.features.frequency_features import FrequencyFeatures
from app.features.gap_features import GapFeatures
from app.features.recency_features import RecencyFeatures

class FeaturePipeline:
    @staticmethod
    def build_features_for_string(target: str, history: List[str]) -> Dict[str, Any]:
        """
        Extracts all static and temporal features for a target string (e.g., '12' for last_two)
        given the chronological list of historical outcomes leading up to this draw.
        """
        features = {}
        
        # 1. Digit Features
        features["first_digit"] = DigitFeatures.get_first_digit(target)
        features["last_digit"] = DigitFeatures.get_last_digit(target)
        features["parity"] = DigitFeatures.get_parity(target)
        features["digit_sum"] = DigitFeatures.get_digit_sum(target)
        features["unique_digit_count"] = DigitFeatures.get_unique_digit_count(target)
        
        # 2. Pattern Features
        features["has_repeated_digits"] = PatternFeatures.has_repeated_digits(target)
        features["has_consecutive_digits"] = PatternFeatures.has_consecutive_digits(target)
        features["odd_even_ratio"] = PatternFeatures.get_odd_even_ratio(target)
        features["high_low_ratio"] = PatternFeatures.get_high_low_ratio(target)
        
        # 3. Frequency Features
        features["digit_frequency"] = FrequencyFeatures.get_digit_frequency(history, target)
        features["rolling_freq_5"] = FrequencyFeatures.get_rolling_frequency(history, target, 5)
        features["rolling_freq_10"] = FrequencyFeatures.get_rolling_frequency(history, target, 10)
        features["moving_avg_10"] = FrequencyFeatures.get_moving_average(history, target, 10)
        features["normalized_frequency"] = FrequencyFeatures.get_normalized_frequency(history, target)
        
        # 4. Gap Features
        features["gap_since_last"] = GapFeatures.get_gap_since_last(history, target)
        features["average_gap"] = GapFeatures.get_average_gap(history, target)
        features["max_gap"] = GapFeatures.get_max_gap(history, target)
        features["current_missing_streak"] = GapFeatures.get_current_missing_streak(history, target)
        
        # 5. Recency Features
        features["recent_occurrence_10"] = RecencyFeatures.get_recent_occurrence(history, target, 10)
        features["weighted_recency"] = RecencyFeatures.get_weighted_recency(history, target)
        features["exponential_decay"] = RecencyFeatures.get_exponential_decay(history, target, 0.5)
        
        return features
