import pytest
from app.features.digit_features import DigitFeatures
from app.features.pattern_features import PatternFeatures
from app.features.frequency_features import FrequencyFeatures
from app.features.gap_features import GapFeatures
from app.features.recency_features import RecencyFeatures
from app.features.feature_pipeline import FeaturePipeline

def test_digit_features():
    assert DigitFeatures.get_first_digit("123") == 1
    assert DigitFeatures.get_last_digit("123") == 3
    assert DigitFeatures.get_middle_digits("123") == "2"
    assert DigitFeatures.get_parity("12") == 0
    assert DigitFeatures.get_parity("13") == 1
    assert DigitFeatures.get_digit_sum("123") == 6
    assert DigitFeatures.get_unique_digit_count("112") == 2
    assert DigitFeatures.get_first_digit("") == -1

def test_pattern_features():
    assert PatternFeatures.has_repeated_digits("112") == 1
    assert PatternFeatures.has_repeated_digits("121") == 0
    assert PatternFeatures.has_consecutive_digits("12") == 1
    assert PatternFeatures.has_consecutive_digits("54") == 1
    assert PatternFeatures.has_consecutive_digits("13") == 0
    assert PatternFeatures.get_odd_even_ratio("132") == 2.0 / 3.0
    assert PatternFeatures.get_high_low_ratio("615") == 2.0 / 3.0

def test_frequency_features():
    history = ["10", "20", "10", "30", "10"]
    assert FrequencyFeatures.get_digit_frequency(history, "10") == 3
    assert FrequencyFeatures.get_rolling_frequency(history, "10", 3) == 2
    assert FrequencyFeatures.get_moving_average(history, "10", 3) == 2.0 / 3.0
    assert FrequencyFeatures.get_normalized_frequency(history, "10") == 3.0 / 5.0
    assert FrequencyFeatures.get_digit_frequency([], "10") == 0

def test_gap_features():
    history = ["10", "20", "30", "10", "40"]
    # 10 is at idx 0 and idx 3
    # reverse is ["40", "10", "30", "20", "10"]
    # get_gap_since_last of "10" is 1 (the "40")
    assert GapFeatures.get_gap_since_last(history, "10") == 1
    assert GapFeatures.get_current_missing_streak(history, "10") == 1
    
    # average gap for 10
    # indices: [0, 3] -> gaps: [3-0-1] = [2]
    assert GapFeatures.get_average_gap(history, "10") == 2.0
    
    # max gap for 10
    # gaps inside: [2]
    # gap to start: 0
    # gap to end: 5 - 1 - 3 = 1
    assert GapFeatures.get_max_gap(history, "10") == 2

def test_recency_features():
    history = ["10", "20", "30"]
    assert RecencyFeatures.get_recent_occurrence(history, "10", 5) == 1
    # weighted recency: max sum = 3*4/2 = 6
    # 10 is at index 0 => weight = 1
    assert RecencyFeatures.get_weighted_recency(history, "10") == 1.0 / 6.0
    # 30 is at index 2 => weight = 3
    assert RecencyFeatures.get_weighted_recency(history, "30") == 3.0 / 6.0
    
    # exponential decay:
    # 10 is at gap k=2 from the end
    # alpha=0.5 -> (0.5)^2 = 0.25
    assert RecencyFeatures.get_exponential_decay(history, "10", 0.5) == 0.25
    
def test_feature_pipeline():
    history = ["12", "34", "12", "56"]
    target = "12"
    features = FeaturePipeline.build_features_for_string(target, history)
    
    assert features["first_digit"] == 1
    assert features["digit_frequency"] == 2
    assert features["gap_since_last"] == 1
    assert features["has_repeated_digits"] == 0
    assert "exponential_decay" in features
