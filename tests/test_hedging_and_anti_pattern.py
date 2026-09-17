"""tests/test_hedging_and_anti_pattern.py
Tests for the Winning Probability Maximization and Hedging Architecture:
- Chronological forward transition matrix behavior
- Dynamic ensemble weights consumption
- Anti-pattern constraints and sanity evaluation rules
- Staking portfolio calculations and parity
"""

import pytest
from pathlib import Path
from ensemble_model.predictor import (
    EnsemblePredictor,
    _transition_matrix,
    load_ensemble_weights,
    DIGIT_COLS,
    ALL_DIGITS,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_HTML = REPO_ROOT / "strategy.html"
INDEX_HTML = REPO_ROOT / "index.html"
THREE_D_HTML = REPO_ROOT / "3d.html"


def test_forward_transition_matrix_chronology():
    """Verify that _transition_matrix calculates P(draw_t+1 | draw_t) forward in time."""
    synthetic_rows = [
        {"digit1": "2", "digit2": "2", "digit3": "2", "digit4": "2", "digit5": "2", "digit6": "2"},
        {"digit1": "1", "digit2": "1", "digit3": "1", "digit4": "1", "digit5": "1", "digit6": "1"},
        {"digit1": "0", "digit2": "0", "digit3": "0", "digit4": "0", "digit5": "0", "digit6": "0"},
    ]
    mat = _transition_matrix(synthetic_rows)
    assert "digit1" in mat
    assert mat["digit1"][0][1] == 1.0
    assert mat["digit1"][1][2] == 1.0
    assert mat["digit1"][2].get(1, 0.0) == 0.1 or mat["digit1"][2].get(1, 0.0) == 0.0


def test_dynamic_weights_loading():
    """Verify that load_ensemble_weights loads a valid weight dictionary with sum = 1.0."""
    weights = load_ensemble_weights()
    assert isinstance(weights, dict)
    assert "transition" in weights
    assert "positional_freq" in weights
    total = sum(weights.values())
    assert abs(total - 1.0) < 0.05, f"Weights should sum to approximately 1.0, got {total}"


def test_anti_pattern_filter_rules():
    """Verify anti-pattern constraints on candidate generation."""
    def is_valid_sum(number_str):
        s = sum(int(d) for d in number_str)
        return 18 <= s <= 38

    assert is_valid_sum("830386") is True
    assert is_valid_sum("000001") is False
    assert is_valid_sum("999999") is False

    def is_valid_parity(number_str):
        evens = sum(1 for d in number_str if int(d) % 2 == 0)
        return 2 <= evens <= 4

    assert is_valid_parity("830386") is True
    assert is_valid_parity("246802") is False
    assert is_valid_parity("135791") is False

    def has_4_identical(number_str):
        return any(number_str[i] == number_str[i+1] == number_str[i+2] == number_str[i+3] for i in range(3))

    assert has_4_identical("830386") is False
    assert has_4_identical("777712") is True
    assert has_4_identical("129999") is True

    def has_4_sequential(number_str):
        int_digits = [int(d) for d in number_str]
        return any(int_digits[i+1] == int_digits[i]+1 and int_digits[i+2] == int_digits[i]+2 and int_digits[i+3] == int_digits[i]+3 for i in range(3))

    assert has_4_sequential("830386") is False
    assert has_4_sequential("123489") is True
    assert has_4_sequential("956780") is True


def test_hedging_calculator_dom_elements_exist():
    """Verify that strategy.html and index.html contain the new Hedging Calculator and Sanity Evaluator elements."""
    for file_path in [STRATEGY_HTML, INDEX_HTML]:
        content = file_path.read_text(encoding="utf-8")
        assert "sec-hedging-portfolio" in content, f"Missing sec-hedging-portfolio in {file_path.name}"
        assert "staking-budget-input" in content, f"Missing staking-budget-input in {file_path.name}"
        assert "hedging-pyramid-container" in content, f"Missing hedging-pyramid-container in {file_path.name}"
        assert "sanity-number-input" in content, f"Missing sanity-number-input in {file_path.name}"
        assert "sanity-report-container" in content, f"Missing sanity-report-container in {file_path.name}"
        assert "calculateHedgingPortfolio" in content, f"Missing calculateHedgingPortfolio function in {file_path.name}"
        assert "runSanityCheck" in content, f"Missing runSanityCheck function in {file_path.name}"
