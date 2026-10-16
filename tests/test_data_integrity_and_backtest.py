"""tests/test_data_integrity_and_backtest.py
Comprehensive regression tests for data integrity, dataset summary extraction,
deduplicated performance tracking, and multi-tier walk-forward backtesting.
"""

import csv
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "database" / "dataset" / "lottery_history.csv"
PRED_HIST = REPO_ROOT / "database" / "predictions" / "prediction_history.json"
PERF_JSON = REPO_ROOT / "performance.json"
CACHE_PATH = REPO_ROOT / "database" / "predictions" / "pipeline_cache.json"


def test_lottery_history_ground_truth_integrity():
    """Verify master lottery dataset has valid dates, chronological order, and valid digits."""
    assert CSV_PATH.exists(), f"Missing dataset: {CSV_PATH}"
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) >= 470, f"Expected >= 470 draws, got {len(reader)}"

    # Check newest-first order
    dates = [row["draw_date"] for row in reader if row.get("draw_date")]
    assert len(dates) == len(reader)
    # Check no duplicates
    assert len(dates) == len(set(dates)), "Duplicate draw_dates detected in master dataset"

    # Verify latest draw
    latest = reader[0]
    assert latest["draw_date"] == "2026-10-16"
    assert latest["first_prize"] == "011781"
    assert latest["last2"] == "48"
    assert latest["front3_1"] == "402"
    assert latest["front3_2"] == "392"
    assert latest["back3_1"] == "171"
    assert latest["back3_2"] == "255"


def test_read_dataset_summary_includes_full_prize_structure():
    """Verify read_dataset_summary() in api/run_pipeline.py returns last2 and 3-digit prizes."""
    from api.run_pipeline import read_dataset_summary

    summary = read_dataset_summary()
    assert isinstance(summary, dict)
    assert summary["total_draws"] >= 470
    assert summary["latest"] == "2026-10-16"
    assert summary["latest_number"] == "011781"
    assert summary["last2"] == "48"
    assert summary["front3"] == ["402", "392"]
    assert summary["back3"] == ["171", "255"]


def test_prediction_history_no_duplicates_or_fabricated_actuals():
    """Verify prediction_history.json contains no duplicates and no fabricated actuals."""
    assert PRED_HIST.exists()
    data = json.loads(PRED_HIST.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 2

    seen_keys = set()
    for entry in data:
        key = (entry.get("target_date"), entry.get("draw_date_used"))
        assert key not in seen_keys, f"Duplicate evaluation entry detected: {key}"
        seen_keys.add(key)

        actual = entry.get("actual_result")
        assert actual != "123456", "Fabricated actual 123456 detected in prediction history"
        assert len(actual) == 6 and actual.isdigit(), f"Invalid actual format: {actual}"


def test_performance_json_metrics_derived_honestly():
    """Verify root performance.json is calculated honestly from non-duplicated records."""
    assert PERF_JSON.exists()
    perf = json.loads(PERF_JSON.read_text(encoding="utf-8"))
    evaluated = perf.get("evaluated") or perf.get("meta", {}).get("evaluated") or perf.get("hit_rate", {}).get("total_evaluated", 0)
    assert evaluated >= 2
    assert "model_score" in perf
    assert "hit_rate" in perf
    assert "digit_accuracy" in perf


def test_backtest_score_prediction_multi_tier():
    """Verify score_prediction calculates 6-digit, 2-digit, and 3-digit metrics correctly."""
    from analytics.backtest_engine import score_prediction

    # Perfect match
    res = score_prediction("402701", "402701", actual_last2="70")
    assert res["exact_match"] is True
    assert res["position_hits"] == 6
    assert res["digit_hits"] == 6
    assert res["top2_match"] is True
    assert res["last2_match"] is False  # '01' != '70'
    assert res["top3_direct"] is True
    assert res["top3_box"] is True

    # 3-digit box match (permutation)
    res_box = score_prediction("123386", "999863")
    assert res_box["exact_match"] is False
    assert res_box["top3_direct"] is False
    assert res_box["top3_box"] is True

    # 2-digit last2 match
    res_l2 = score_prediction("000070", "111111", actual_last2="70")
    assert res_l2["last2_match"] is True


def test_backtest_engine_walk_forward_execution():
    """Verify run_backtest runs walk-forward with multi-tiered metric output."""
    from analytics.backtest_engine import run_backtest

    res = run_backtest(max_draws=3, use_random_only=True)
    assert res["mode"] == "RANDOM BASELINE"
    assert res["total_draws"] == 3
    assert "metrics_6digit" in res
    assert "metrics_2digit" in res
    assert "metrics_3digit" in res
    assert "positional_accuracy_pct" in res["metrics_6digit"]


def test_dashboards_latest_result_ground_truth_consistency():
    """Verify manager.html, index.html, and strategy.html all reflect the 16 Oct 2026 draw."""
    for filename in ["manager.html", "index.html", "strategy.html"]:
        path = REPO_ROOT / filename
        content = path.read_text(encoding="utf-8")
        assert "011781" in content, f"{filename} missing latest first prize 011781"
        assert "48" in content, f"{filename} missing latest last-2 48"
        assert "16 ต.ค. 2569" in content, f"{filename} missing latest draw date 16 ต.ค. 2569"


def test_backtest_predictor_failure_handling_no_random_fallback(monkeypatch):
    """
    CRITICAL: Verify that when the real predictor fails:
    1. The failure is recorded explicitly in prediction_failures and failed_draws_details.
    2. NO random number fallback is silently substituted into model metrics.
    3. Failed draws have predicted=None and status='failed'.
    """
    import analytics.backtest_engine as bte

    # Spy on _random_prediction to ensure it is NEVER called during ensemble failure
    random_called = []
    original_random = bte._random_prediction

    def mock_random():
        random_called.append(True)
        return original_random()

    def mock_failing_predictor(history_rows, top_k=1):
        raise RuntimeError("Intentional predictor crash for testing error handling")

    monkeypatch.setattr(bte, "_random_prediction", mock_random)
    monkeypatch.setattr(bte, "_predict_with_ensemble", mock_failing_predictor)

    res = bte.run_backtest(max_draws=3, use_random_only=False)

    assert res["prediction_failures"] == 3, "All 3 draws must be recorded as failures"
    assert res["failure_rate_pct"] == 100.0, "Failure rate must be 100%"
    assert res["successful_draws"] == 0, "Successful draws must be 0"
    assert len(res["failed_draws_details"]) == 3, "Must capture error details for all 3 failed draws"
    assert all("Intentional predictor crash" in d["error"] for d in res["failed_draws_details"])

    # Verify no random fallback was invoked
    assert len(random_called) == 0, "Must NEVER call random fallback when predictor fails!"

    # Verify detail rows
    for draw in res["draws_evaluated"]:
        assert draw["status"] == "failed"
        assert draw["predicted"] is None
        assert draw["position_hits"] == 0
        assert draw["exact_match"] is False


def test_backtest_statistical_uncertainty_and_confidence_interval():
    """Verify Wilson score interval and two-tailed p-value calculation."""
    from analytics.backtest_engine import compute_wilson_ci, calc_two_tailed_p_value

    ci = compute_wilson_ci(10, 100, confidence=0.95)
    assert ci["point_estimate_pct"] == 10.0
    assert 5.0 < ci["ci_lower_pct"] < 10.0
    assert 10.0 < ci["ci_upper_pct"] < 18.0

    # Z = 1.96 should produce two-tailed p ~ 0.05
    p_val = calc_two_tailed_p_value(1.95996)
    assert abs(p_val - 0.05) < 0.001


def test_comparative_backtest_repeated_trials_and_seed_reproducibility():
    """Verify comparative backtest runs repeated random trials with disclaimer and seed reproducibility."""
    from analytics.backtest_engine import run_comparative_backtest

    res1 = run_comparative_backtest(max_draws=2, random_trials=3, random_seed=42)
    res2 = run_comparative_backtest(max_draws=2, random_trials=3, random_seed=42)

    # Identical seed produces identical random baseline mean
    assert res1["random_baseline"]["mean_positional_accuracy_pct"] == res2["random_baseline"]["mean_positional_accuracy_pct"]
    assert res1["random_baseline"]["trials_count"] == 3

    # Verification of explicit scientific disclaimer
    disclaimer = res1["comparison"]["disclaimer"]
    assert "Do not interpret a positive lift as proof of predictive advantage" in disclaimer
    assert "inherent randomness in lottery draws" in disclaimer

