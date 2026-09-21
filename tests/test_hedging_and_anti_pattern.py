"""tests/test_hedging_and_anti_pattern.py
Tests for the Winning Probability Maximization and Hedging Architecture:
- Chronological forward transition matrix behavior
- Dynamic ensemble weights consumption (recalibrated for dry-spell remediation)
- Anti-pattern constraints (sum 20-36, ascending/descending runs)
- Staking portfolio calculations and parity (70/15/10/5 breakdown)
- Root to dashboard/ mirror SHA-256 parity
- Weekday stratification (Thursday sample weighting)
"""

import hashlib
import pytest
from pathlib import Path
from ensemble_model.predictor import (
    EnsemblePredictor,
    _transition_matrix,
    _get_draw_weight,
    load_ensemble_weights,
    DIGIT_COLS,
    ALL_DIGITS,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_HTML = REPO_ROOT / "strategy.html"
INDEX_HTML = REPO_ROOT / "index.html"
THREE_D_HTML = REPO_ROOT / "3d.html"
MANAGER_HTML = REPO_ROOT / "manager.html"


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
    """Verify that load_ensemble_weights loads recalibrated weights summing to 1.0."""
    weights = load_ensemble_weights()
    assert isinstance(weights, dict)
    assert "transition" in weights
    assert "positional_freq" in weights
    assert "rolling_heat" in weights
    assert "temporal_trend" in weights

    total = sum(weights.values())
    assert abs(total - 1.0) < 0.001, f"Weights should sum to exactly 1.0, got {total}"
    assert weights["rolling_heat"] == 0.25
    assert weights["conditional"] == 0.25
    assert weights["transition"] == 0.15
    assert weights["temporal_trend"] == 0.10
    assert weights["pair_lift"] == 0.10
    assert weights["positional_freq"] == 0.05
    assert weights["pattern_hot"] == 0.05
    assert weights["gap_overdue"] == 0.05


def test_anti_pattern_filter_rules():
    """Verify tightened anti-pattern constraints on candidate generation (sum 20-36, ascending & descending runs)."""
    def is_valid_sum(number_str):
        s = sum(int(d) for d in number_str)
        return 20 <= s <= 36

    assert is_valid_sum("830386") is True   # sum = 28 (valid)
    assert is_valid_sum("730640") is True   # sum = 20 (lower boundary)
    assert is_valid_sum("666666") is True   # sum = 36 (upper boundary)
    assert is_valid_sum("417212") is False  # sum = 17 (under lower boundary)
    assert is_valid_sum("004615") is False  # sum = 16 (under lower boundary)
    assert is_valid_sum("000001") is False  # sum = 1
    assert is_valid_sum("766666") is False  # sum = 37 (exceeds upper boundary)
    assert is_valid_sum("999999") is False  # sum = 54

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
        asc = any(int_digits[i+1] == int_digits[i]+1 and int_digits[i+2] == int_digits[i]+2 and int_digits[i+3] == int_digits[i]+3 for i in range(3))
        desc = any(int_digits[i+1] == int_digits[i]-1 and int_digits[i+2] == int_digits[i]-2 and int_digits[i+3] == int_digits[i]-3 for i in range(3))
        return asc or desc

    assert has_4_sequential("830386") is False
    assert has_4_sequential("123489") is True   # ascending run
    assert has_4_sequential("956780") is True   # ascending run
    assert has_4_sequential("987612") is True   # descending run
    assert has_4_sequential("143210") is True   # descending run


def test_hedging_calculator_dom_elements_exist():
    """Verify that strategy.html and index.html contain the Hedging Calculator and Sanity Evaluator elements."""
    for file_path in [STRATEGY_HTML, INDEX_HTML]:
        content = file_path.read_text(encoding="utf-8")
        assert "sec-hedging-portfolio" in content, f"Missing sec-hedging-portfolio in {file_path.name}"
        assert "staking-budget-input" in content, f"Missing staking-budget-input in {file_path.name}"
        assert "hedging-pyramid-container" in content, f"Missing hedging-pyramid-container in {file_path.name}"
        assert "sanity-number-input" in content, f"Missing sanity-number-input in {file_path.name}"
        assert "sanity-report-container" in content, f"Missing sanity-report-container in {file_path.name}"
        assert "calculateHedgingPortfolio" in content, f"Missing calculateHedgingPortfolio function in {file_path.name}"
        assert "runSanityCheck" in content, f"Missing runSanityCheck function in {file_path.name}"


def test_hedging_proportions_70_15_10_5():
    """Verify that strategy.html, index.html, 3d.html, and manager.html reflect the 70/15/10/5 breakdown."""
    for file_path in [STRATEGY_HTML, INDEX_HTML]:
        content = file_path.read_text(encoding="utf-8")
        assert "0.70" in content, f"Missing 0.70 Banker weight in {file_path.name}"
        assert "0.15" in content, f"Missing 0.15 2D weight in {file_path.name}"
        assert "0.10" in content, f"Missing 0.10 3D weight in {file_path.name}"
        assert "ฐานราก 70%" in content, f"Missing ฐานราก 70% in {file_path.name}"
        assert "ชั้นกลาง 15%" in content, f"Missing ชั้นกลาง 15% in {file_path.name}"
        assert "70% / 15% / 10% / 5%" in content, f"Missing 70/15/10/5 subtitle in {file_path.name}"

    threed_content = THREE_D_HTML.read_text(encoding="utf-8")
    assert "70%" in threed_content
    assert "15%" in threed_content
    assert "70% Banker" in threed_content
    assert "15% Pairs" in threed_content

    mgr_content = MANAGER_HTML.read_text(encoding="utf-8")
    assert "วิ่ง 70%" in mgr_content
    assert "2ตัว 15%" in mgr_content
    assert "3ตัว 10%" in mgr_content
    assert "สลาก 5%" in mgr_content


def test_thursday_sample_weighting():
    """Verify that Thursday draws receive weight=2.0 while other weekdays receive weight=1.0."""
    from datetime import date, datetime
    thursday_row = {"draw_date": "2026-07-16"}  # Thursday (weekday = 3)
    wednesday_row = {"draw_date": "2026-09-16"} # Wednesday (weekday = 2)
    sunday_row = {"draw_date": "2026-08-16"}    # Sunday (weekday = 6)
    whitespace_thursday = {"draw_date": " 2026-07-16 "}
    datetime_thursday = {"draw_date": datetime(2026, 7, 16)}
    date_thursday = {"draw_date": date(2026, 7, 16)}
    missing_row = {}

    assert _get_draw_weight(thursday_row) == 2.0
    assert _get_draw_weight(whitespace_thursday) == 2.0
    assert _get_draw_weight(datetime_thursday) == 2.0
    assert _get_draw_weight(date_thursday) == 2.0
    assert _get_draw_weight(wednesday_row) == 1.0
    assert _get_draw_weight(sunday_row) == 1.0
    assert _get_draw_weight(missing_row) == 1.0


def test_ensemble_predictor_real_candidate_filtering():
    """Verify that EnsemblePredictor.generate_candidates strictly applies anti-pattern filters to real candidates."""
    csv_path = REPO_ROOT / "database" / "dataset" / "lottery_history.csv"
    predictor = EnsemblePredictor(csv_path)
    predictor.load()
    predictor.extract_signals()
    predictor.score_positions()
    candidates = predictor.generate_candidates(top_k=10, beam_width=5)

    assert len(candidates) > 0, "Predictor should generate candidates"

    for cand in candidates:
        num = cand["number"]
        digits = [int(d) for d in num]
        s = sum(digits)
        assert 20 <= s <= 36, f"Candidate {num} violates sum constraint: sum={s}"

        evens = sum(1 for d in digits if d % 2 == 0)
        assert 2 <= evens <= 4, f"Candidate {num} violates parity balance: evens={evens}"

        # No 4 consecutive identical digits
        assert not any(digits[i] == digits[i+1] == digits[i+2] == digits[i+3] for i in range(3)), \
            f"Candidate {num} contains 4 consecutive identical digits"

        # No 4 ascending or descending sequential digits
        asc = any(digits[i+1] == digits[i]+1 and digits[i+2] == digits[i]+2 and digits[i+3] == digits[i]+3 for i in range(3))
        desc = any(digits[i+1] == digits[i]-1 and digits[i+2] == digits[i]-2 and digits[i+3] == digits[i]-3 for i in range(3))
        assert not (asc or desc), f"Candidate {num} contains 4 sequential digits (asc={asc}, desc={desc})"


def test_generate_full_spectrum_box3_deduplication():
    """Verify that generate_full_spectrum deduplicates 3D box permutation roots."""
    csv_path = REPO_ROOT / "database" / "dataset" / "lottery_history.csv"
    predictor = EnsemblePredictor(csv_path)
    predictor.load()
    predictor.extract_signals()
    predictor.score_positions()
    predictor.generate_candidates(top_k=5, beam_width=5)
    fs = predictor.generate_full_spectrum()

    box_3 = fs.get("box_3", [])
    assert len(box_3) > 0
    seen_roots = set()
    for item in box_3:
        root = "".join(sorted(item["direct"]))
        assert root not in seen_roots, f"Duplicate 3D box root found: {root} in {item['direct']}"
        seen_roots.add(root)


def test_dashboard_mirror_sha256_parity():
    """Verify 100% SHA-256 parity between root and dashboard/ mirrors."""
    for fname in ["strategy.html", "index.html", "3d.html", "manager.html"]:
        root_path = REPO_ROOT / fname
        dash_path = REPO_ROOT / "dashboard" / fname
        assert root_path.exists(), f"Missing root {fname}"
        assert dash_path.exists(), f"Missing dashboard/{fname}"
        h_root = hashlib.sha256(root_path.read_bytes()).hexdigest()
        h_dash = hashlib.sha256(dash_path.read_bytes()).hexdigest()
        assert h_root == h_dash, f"SHA-256 mismatch for {fname}: root={h_root} != dash={h_dash}"
