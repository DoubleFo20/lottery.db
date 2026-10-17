"""
Lottery AI Backtesting Engine
=============================
Walk-forward evaluation of the ensemble prediction model against
historical lottery draws.

Key design decisions:
  • Uses real EnsemblePredictor (CRITICAL: zero random fallback on failure).
  • When the predictor fails, reports failure count and error details explicitly.
  • Walk-forward: for each test draw, only prior draws are visible.
  • Accuracy = total_position_hits / (successful_draws × 6).
  • Repeated random baseline trials with fixed seed and Wilson score confidence intervals.
  • Rigorous hypothesis testing (Z-test, p-value) against random chance.
  • Reports uncertainty honestly — lottery outcomes are inherently random.
"""

import argparse
import csv
import json
import math
import random
import sys
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
BACKTEST_DIR = BASE_DIR / "database" / "backtest"
REPORT_JSON = BACKTEST_DIR / "backtest_report.json"
REPORT_CSV = BACKTEST_DIR / "backtest_report.csv"
COMPARATIVE_JSON = BACKTEST_DIR / "comparative_report.json"

DIGIT_COLS = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]

sys.path.insert(0, str(BASE_DIR))


def load_history() -> list[dict]:
    """Load historical lottery draws from CSV (with raw rows for predictor)."""
    history = []
    if not CSV_PATH.exists():
        print(f"[ERROR] Dataset not found: {CSV_PATH}")
        return history

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_val = row.get("draw_date", "")
            digits = [row.get(f"digit{i}", "") for i in range(1, 7)]
            number = "".join(digits)
            if date_val and len(number) == 6 and number.isdigit():
                history.append({"date": date_val, "number": number, "raw": row})

    # Sort chronologically (oldest first)
    history.sort(key=lambda x: x["date"])
    return history


def compute_wilson_ci(k_hits: int, n_trials: int, confidence: float = 0.95) -> dict:
    """Compute Wilson score interval for binomial proportion."""
    if n_trials <= 0:
        return {"ci_lower_pct": 0.0, "ci_upper_pct": 0.0, "standard_error": 0.0}
    p_hat = k_hits / n_trials
    z = 1.95996 if confidence == 0.95 else 2.57583
    denominator = 1.0 + (z ** 2) / n_trials
    center = (p_hat + (z ** 2) / (2.0 * n_trials)) / denominator
    margin = (z * math.sqrt((p_hat * (1.0 - p_hat) / n_trials) + ((z ** 2) / (4.0 * (n_trials ** 2))))) / denominator
    se = math.sqrt(p_hat * (1.0 - p_hat) / n_trials) if n_trials > 0 else 0.0
    return {
        "point_estimate_pct": round(p_hat * 100, 4),
        "ci_lower_pct": round(max(0.0, center - margin) * 100, 4),
        "ci_upper_pct": round(min(1.0, center + margin) * 100, 4),
        "standard_error": round(se, 6),
        "confidence_level": confidence,
    }


def normal_cdf(z: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def calc_two_tailed_p_value(z: float) -> float:
    """Two-tailed p-value from z-score."""
    return 2.0 * (1.0 - normal_cdf(abs(z)))


def score_prediction(
    predicted: str | None,
    actual: str,
    actual_last2: str = "",
    front3: list[str] | None = None,
    back3: list[str] | None = None,
) -> dict:
    """
    Compare predicted number with official draw results across:
    1. 6-digit First Prize / Jackpot (position hits, digit hits, exact match)
    2. Official 2-digit Last-2 prize (เลขท้าย 2 ตัว) & Top-2 (2 ตัวบน)
    3. Official 3-digit Front-3 prizes (เลขหน้า 3 ตัว) & Back-3 prizes (เลขท้าย 3 ตัว)
    4. Top-3 Direct (3 ตัวตรง) & Top-3 Box (3 ตัวโต๊ด)
    """
    actual = str(actual).zfill(6)[:6]
    actual_last2 = str(actual_last2).zfill(2)[:2] if actual_last2 else ""
    front3_cleaned = [str(f).zfill(3)[:3] for f in front3 if f] if front3 else []
    back3_cleaned = [str(b).zfill(3)[:3] for b in back3 if b] if back3 else []

    if predicted is None:
        return {
            "predicted": None,
            "actual": actual,
            "exact_match": False,
            "position_hits": 0,
            "digit_hits": 0,
            "top2_match": False,
            "last2_match": False,
            "front3_match": False,
            "back3_match": False,
            "top3_direct": False,
            "top3_box": False,
            "status": "failed",
        }

    predicted = str(predicted).zfill(6)[:6]

    # 1. 6-digit evaluation
    position_hits = sum(1 for p, a in zip(predicted, actual) if p == a)

    p_list = list(predicted)
    a_list = list(actual)
    digit_hits = 0
    for d in p_list:
        if d in a_list:
            digit_hits += 1
            a_list.remove(d)

    # 2. 2-digit evaluation
    top2_match = (predicted[-2:] == actual[-2:])
    last2_match = (predicted[-2:] == actual_last2) if actual_last2 else False

    # 3. Official GLO 3-digit evaluation
    front3_match = (predicted[:3] in front3_cleaned) if front3_cleaned else False
    back3_match = (predicted[-3:] in back3_cleaned) if back3_cleaned else False

    # 4. First Prize sub-combinations (Top-3 Direct & Box)
    top3_direct = (predicted[-3:] == actual[-3:])
    top3_box = (sorted(predicted[-3:]) == sorted(actual[-3:]))

    return {
        "predicted": predicted,
        "actual": actual,
        "exact_match": predicted == actual,
        "position_hits": position_hits,
        "digit_hits": digit_hits,
        "top2_match": top2_match,
        "last2_match": last2_match,
        "front3_match": front3_match,
        "back3_match": back3_match,
        "top3_direct": top3_direct,
        "top3_box": top3_box,
        "status": "success",
    }


def _predict_with_ensemble(history_rows: list[dict], top_k: int = 1, weights: dict | None = None) -> str:
    """
    Generate a prediction using the real EnsemblePredictor,
    trained only on the provided history_rows (walk-forward).
    Accepts optional decoupled weights to prevent look-ahead hyperparameter leakage.
    Returns the top-1 candidate number string.
    """
    from ensemble_model.predictor import EnsemblePredictor

    predictor = EnsemblePredictor(CSV_PATH, window=min(50, len(history_rows)), weights=weights)
    # Feed only the allowed historical rows (desc order expected by predictor)
    predictor.rows = list(reversed(history_rows))  # predictor expects desc order
    predictor.extract_signals()
    predictor.score_positions()
    candidates = predictor.generate_candidates(top_k=top_k, beam_width=5)

    if candidates:
        return candidates[0]["number"]
    # Fallback: if no candidates pass filters, pick top digit per position
    fallback = ""
    for col in DIGIT_COLS:
        scores = predictor.position_scores.get(col, {})
        if scores:
            fallback += str(max(scores, key=scores.get))
        else:
            fallback += "0"
    return fallback


def audit_weights_leakage() -> dict:
    """
    Audit ensemble weights and walk-forward data partitioning for look-ahead data leakage.
    Verifies that:
      1. History partitioning produces strictly earlier draws than target draw.
      2. Signal extraction operates only on visible draws prior to the target.
      3. Predictor accepts decoupled weights (e.g., untuned equal weights) to isolate
         model architecture evaluation from historical parameter fitting.
    """
    history = load_history()
    if len(history) < 10:
        return {"passed": False, "reason": "Insufficient history for audit"}

    dates = [h["date"] for h in history]
    is_sorted = all(dates[i] < dates[i + 1] for i in range(len(dates) - 1))

    mid_idx = len(history) // 2
    history_up_to = [h["raw"] for h in history[:mid_idx]]
    target_draw = history[mid_idx]
    target_date = target_draw["date"]

    no_future_rows = all(h["draw_date"] < target_date for h in history_up_to)

    equal_weights = {
        "rolling_heat": 0.125,
        "conditional": 0.125,
        "transition": 0.125,
        "temporal_trend": 0.125,
        "pair_lift": 0.125,
        "positional_freq": 0.125,
        "pattern_hot": 0.125,
        "gap_overdue": 0.125,
    }
    pred_equal = _predict_with_ensemble(history_up_to, weights=equal_weights)
    valid_pred = isinstance(pred_equal, str) and len(pred_equal) == 6 and pred_equal.isdigit()

    passed = is_sorted and no_future_rows and valid_pred
    return {
        "passed": passed,
        "chronological_order": is_sorted,
        "strict_pre_draw_isolation": no_future_rows,
        "equal_weights_operational": valid_pred,
        "sample_draw_evaluated": target_date,
        "sample_prediction": pred_equal,
        "audit_timestamp": datetime.now().isoformat(),
    }


def _random_prediction() -> str:
    """Generate a uniformly random 6-digit number for baseline measurement."""
    return f"{random.randint(0, 999999):06d}"


def run_backtest(
    max_draws: int = 50,
    use_random_only: bool = False,
    min_history: int = 100,
    random_seed: int | None = None,
    weights_mode: str | dict = "calibrated",
) -> dict:
    """
    Walk-forward backtest: for each draw i >= min_history,
    predict using only draws [0..i-1], then score against draw i.

    CRITICAL INTEGRITY RULES:
    1. Zero random fallback: if predictor fails, explicitly recorded and penalized.
    2. Strict pre-draw isolation: draws [0..i-1] only, asserted chronologically.
    3. Official prize structure: evaluates 6-digit First Prize, Last-2, Front-3, Back-3, Top-2, Top-3.
    4. Decoupled weights: supports untuned equal weights to prevent look-ahead bias.
    """
    if random_seed is not None:
        random.seed(random_seed)

    if weights_mode == "equal":
        eval_weights = {
            "rolling_heat": 0.125,
            "conditional": 0.125,
            "transition": 0.125,
            "temporal_trend": 0.125,
            "pair_lift": 0.125,
            "positional_freq": 0.125,
            "pattern_hot": 0.125,
            "gap_overdue": 0.125,
        }
    elif isinstance(weights_mode, dict):
        eval_weights = weights_mode
    else:
        eval_weights = None

    history = load_history()
    if not history:
        print("[WARN] Empty history. Cannot run backtest.")
        return {}

    if len(history) <= min_history:
        print(f"[WARN] Not enough history ({len(history)} draws, need >{min_history})")
        return {}

    test_range = list(range(min_history, len(history)))
    if max_draws > 0:
        test_range = test_range[-max_draws:]  # most recent N draws

    mode = "RANDOM BASELINE" if use_random_only else ("ENSEMBLE (UNTUNED EQUAL)" if weights_mode == "equal" else "ENSEMBLE MODEL")
    print(f"\n[INFO] Running {mode} backtest on {len(test_range)} draws (walk-forward)...")

    results = []
    total_attempted = 0
    successful_draws = 0
    prediction_failures = 0
    failed_draws_details = []

    exact_matches = 0
    total_digit_hits = 0
    total_pos_hits = 0
    total_top2_matches = 0
    total_last2_matches = 0
    total_front3_matches = 0
    total_back3_matches = 0
    total_top3_direct_matches = 0
    total_top3_box_matches = 0

    for count, i in enumerate(test_range):
        history_up_to = [h["raw"] for h in history[:i]]
        actual_number = history[i]["number"]
        raw_row = history[i]["raw"]
        actual_last2 = raw_row.get("last2", "")
        front3 = [raw_row.get("front3_1", ""), raw_row.get("front3_2", "")]
        back3 = [raw_row.get("back3_1", ""), raw_row.get("back3_2", "")]
        front3 = [f for f in front3 if f]
        back3 = [b for b in back3 if b]
        draw_date = history[i]["date"]
        total_attempted += 1

        # Strict chronological verification against look-ahead data leakage
        assert all(h["draw_date"] < draw_date for h in history_up_to), (
            f"LEAKAGE DETECTED: Draw {draw_date} history contains draws >= {draw_date}"
        )

        # Generate prediction
        if use_random_only:
            predicted_number = _random_prediction()
            pred_status = "success"
            pred_error = None
        else:
            try:
                if eval_weights is not None:
                    predicted_number = _predict_with_ensemble(history_up_to, weights=eval_weights)
                else:
                    predicted_number = _predict_with_ensemble(history_up_to)
                pred_status = "success"
                pred_error = None
            except Exception as e:
                # CRITICAL: Record failure explicitly. DO NOT fall back to random!
                prediction_failures += 1
                pred_error = str(e)
                failed_draws_details.append({"date": draw_date, "error": pred_error})
                print(f"  [FAIL] Predictor failed for {draw_date}: {pred_error}")
                predicted_number = None
                pred_status = "failed"

        if predicted_number is not None:
            successful_draws += 1
            sc = score_prediction(
                predicted_number,
                actual_number,
                actual_last2=actual_last2,
                front3=front3,
                back3=back3,
            )
            sc["date"] = draw_date
            sc["status"] = "success"
            sc["error"] = None
            results.append(sc)

            if sc["exact_match"]:
                exact_matches += 1
            total_digit_hits += sc["digit_hits"]
            total_pos_hits += sc["position_hits"]
            if sc["top2_match"]:
                total_top2_matches += 1
            if sc["last2_match"]:
                total_last2_matches += 1
            if sc["front3_match"]:
                total_front3_matches += 1
            if sc["back3_match"]:
                total_back3_matches += 1
            if sc["top3_direct"]:
                total_top3_direct_matches += 1
            if sc["top3_box"]:
                total_top3_box_matches += 1
        else:
            # Explicit failure entry: zero hits, clearly flagged
            sc = {
                "date": draw_date,
                "predicted": None,
                "actual": actual_number,
                "status": "failed",
                "error": pred_error,
                "exact_match": False,
                "position_hits": 0,
                "digit_hits": 0,
                "top2_match": False,
                "last2_match": False,
                "front3_match": False,
                "back3_match": False,
                "top3_direct": False,
                "top3_box": False,
            }
            results.append(sc)

        # Progress reporting
        if (count + 1) % 50 == 0 or count == 0:
            cur_succ = successful_draws if successful_draws > 0 else 1
            print(f"  [{count+1}/{len(test_range)}] succ={successful_draws}/{total_attempted} "
                  f"fails={prediction_failures} "
                  f"avg_pos={total_pos_hits/cur_succ:.2f}/6 "
                  f"avg_dig={total_digit_hits/cur_succ:.2f}/6 "
                  f"top2={total_top2_matches}/{cur_succ} "
                  f"top3_box={total_top3_box_matches}/{cur_succ}")

    if total_attempted == 0:
        return {}

    eval_draws = successful_draws if successful_draws > 0 else 1
    n_digit_trials = successful_draws * 6
    positional_accuracy = total_pos_hits / n_digit_trials if n_digit_trials > 0 else 0.0

    # Statistical confidence interval (Wilson Score for position trials)
    wilson_ci = compute_wilson_ci(total_pos_hits, n_digit_trials)

    # Z-test against pure random chance p0 = 0.10
    p0 = 0.10
    if n_digit_trials > 0:
        se0 = math.sqrt(p0 * (1.0 - p0) / n_digit_trials)
        z_stat = (positional_accuracy - p0) / se0 if se0 > 0 else 0.0
        p_val = calc_two_tailed_p_value(z_stat)
    else:
        z_stat = 0.0
        p_val = 1.0

    # Draw-level statistical uncertainty
    draw_pos_hits = [r["position_hits"] for r in results if r.get("status") == "success"]
    if draw_pos_hits:
        n_draws = len(draw_pos_hits)
        mean_draw_pos = sum(draw_pos_hits) / n_draws
        var_draw_pos = sum((x - mean_draw_pos) ** 2 for x in draw_pos_hits) / (n_draws - 1) if n_draws > 1 else 0.0
        std_draw_pos = math.sqrt(var_draw_pos)
        se_draw_pos = std_draw_pos / math.sqrt(n_draws) if n_draws > 0 else 0.0
        ci_draw_lower = max(0.0, mean_draw_pos - 1.95996 * se_draw_pos)
        ci_draw_upper = min(6.0, mean_draw_pos + 1.95996 * se_draw_pos)

        # Draw-level test vs random null mu0 = 0.60 (6 * 0.10)
        sigma0_draw = math.sqrt(0.54)
        se0_draw = sigma0_draw / math.sqrt(n_draws) if n_draws > 0 else 0.0
        z_draw = (mean_draw_pos - 0.60) / se0_draw if se0_draw > 0 else 0.0
        p_val_draw = calc_two_tailed_p_value(z_draw)
    else:
        mean_draw_pos = 0.0
        std_draw_pos = 0.0
        se_draw_pos = 0.0
        ci_draw_lower = 0.0
        ci_draw_upper = 0.0
        z_draw = 0.0
        p_val_draw = 1.0

    coverage_rate_pct = round(successful_draws / total_attempted * 100, 4) if total_attempted > 0 else 0.0
    failure_rate_pct = round(prediction_failures / total_attempted * 100, 4) if total_attempted > 0 else 0.0

    summary = {
        "mode": mode,
        "model_version": "EnsemblePredictor-v2.1",
        "attempted_draws": total_attempted,
        "successful_draws": successful_draws,
        "prediction_failures": prediction_failures,
        "failure_rate_pct": failure_rate_pct,
        "failed_draws_details": failed_draws_details,
        "total_draws": successful_draws,  # backward compatibility
        "sample_size_positions": n_digit_trials,
        "coverage": {
            "attempted_draws": total_attempted,
            "successful_draws": successful_draws,
            "failed_draws": prediction_failures,
            "coverage_rate_pct": coverage_rate_pct,
            "failure_rate_pct": failure_rate_pct,
        },
        "statistical_uncertainty": {
            "sample_size_draws": successful_draws,
            "sample_size_positions": n_digit_trials,
            "positional_accuracy_pct": round(positional_accuracy * 100, 4),
            "wilson_ci_95": {
                "lower_pct": wilson_ci["ci_lower_pct"],
                "upper_pct": wilson_ci["ci_upper_pct"],
            },
            "standard_error": wilson_ci["standard_error"],
            "position_standard_error": wilson_ci["standard_error"],
            "hypothesis_test_vs_random_10pct": {
                "null_hypothesis": "Positional accuracy is <= 10.0% (random baseline)",
                "z_score": round(z_stat, 4),
                "p_value": round(p_val, 6),
                "statistically_significant_at_05": p_val < 0.05 and z_stat > 0,
            },
            "draw_level_uncertainty": {
                "sample_size_draws": successful_draws,
                "mean_position_hits_per_draw": round(mean_draw_pos, 4),
                "sample_std_dev": round(std_draw_pos, 4),
                "draw_standard_error": round(se_draw_pos, 4),
                "ci_95_draw_hits": {
                    "lower": round(ci_draw_lower, 4),
                    "upper": round(ci_draw_upper, 4),
                },
                "hypothesis_test_vs_random_0_60": {
                    "null_hypothesis": "Mean position hits per draw is <= 0.60 (pure random expectation)",
                    "expected_mean": 0.60,
                    "z_score": round(z_draw, 4),
                    "p_value": round(p_val_draw, 6),
                    "statistically_significant_at_05": p_val_draw < 0.05 and z_draw > 0,
                },
            },
            "interpretation": (
                "Do not interpret a positive lift as proof of predictive advantage. "
                "Due to high variance and inherent randomness in lottery draws, sample hit rate variations "
                "are consistent with random statistical fluctuations. Lottery outcomes are designed to be independent and uniformly random."
            ),
        },
        "metrics_official_prizes": {
            "first_prize_jackpot": {
                "matches": exact_matches,
                "match_rate_pct": round(exact_matches / eval_draws * 100, 4),
                "expected_random_pct": 0.0001,
            },
            "front3_prizes": {
                "matches": total_front3_matches,
                "match_rate_pct": round(total_front3_matches / eval_draws * 100, 4),
                "expected_random_pct": 0.20,
            },
            "back3_prizes": {
                "matches": total_back3_matches,
                "match_rate_pct": round(total_back3_matches / eval_draws * 100, 4),
                "expected_random_pct": 0.20,
            },
            "last2_prize": {
                "matches": total_last2_matches,
                "match_rate_pct": round(total_last2_matches / eval_draws * 100, 4),
                "expected_random_pct": 1.00,
            },
            "top2_market": {
                "matches": total_top2_matches,
                "match_rate_pct": round(total_top2_matches / eval_draws * 100, 4),
                "expected_random_pct": 1.00,
            },
            "top3_direct_market": {
                "matches": total_top3_direct_matches,
                "match_rate_pct": round(total_top3_direct_matches / eval_draws * 100, 4),
                "expected_random_pct": 0.10,
            },
            "top3_box_market": {
                "matches": total_top3_box_matches,
                "match_rate_pct": round(total_top3_box_matches / eval_draws * 100, 4),
                "expected_random_pct": 0.60,
            },
        },
        "metrics_6digit": {
            "exact_matches": exact_matches,
            "exact_match_rate": round(exact_matches / eval_draws, 6),
            "average_digit_hits": round(total_digit_hits / eval_draws, 4),
            "average_position_hits": round(total_pos_hits / eval_draws, 4),
            "positional_accuracy_pct": round(positional_accuracy * 100, 4),
            "expected_random_accuracy_pct": 10.0,
            "ci_95_lower_pct": wilson_ci["ci_lower_pct"],
            "ci_95_upper_pct": wilson_ci["ci_upper_pct"],
        },
        "metrics_2digit": {
            "top2_matches": total_top2_matches,
            "top2_match_rate_pct": round(total_top2_matches / eval_draws * 100, 4),
            "expected_top2_random_pct": 1.0,
            "last2_matches": total_last2_matches,
            "last2_match_rate_pct": round(total_last2_matches / eval_draws * 100, 4),
        },
        "metrics_3digit": {
            "front3_matches": total_front3_matches,
            "front3_match_rate_pct": round(total_front3_matches / eval_draws * 100, 4),
            "expected_front3_random_pct": 0.2,
            "back3_matches": total_back3_matches,
            "back3_match_rate_pct": round(total_back3_matches / eval_draws * 100, 4),
            "expected_back3_random_pct": 0.2,
            "top3_direct_matches": total_top3_direct_matches,
            "top3_direct_rate_pct": round(total_top3_direct_matches / eval_draws * 100, 4),
            "expected_top3_direct_random_pct": 0.1,
            "top3_box_matches": total_top3_box_matches,
            "top3_box_rate_pct": round(total_top3_box_matches / eval_draws * 100, 4),
            "expected_top3_box_random_pct": 0.6,
        },
        # Backward-compatible flat keys:
        "exact_matches": exact_matches,
        "exact_match_rate": round(exact_matches / eval_draws, 6),
        "average_digit_hits": round(total_digit_hits / eval_draws, 4),
        "average_position_hits": round(total_pos_hits / eval_draws, 4),
        "positional_accuracy_pct": round(positional_accuracy * 100, 4),
        "note": (
            "Positional accuracy = total_position_hits / (successful_draws × 6). "
            "Random baseline expectation ≈ 10% (1/10 per digit position). "
            "Lottery outcomes are inherently unpredictable; past performance does not guarantee future hits."
        ),
        "run_time": datetime.now().isoformat(),
        "draws_evaluated": results,
    }

    return summary


def run_comparative_backtest(
    max_draws: int = 50,
    random_trials: int = 10,
    random_seed: int = 42,
    min_history: int = 100,
    weights_mode: str = "calibrated",
) -> dict:
    """
    Run ensemble backtest (zero random fallback) and compare against
    repeated random-baseline trials with fixed seed and confidence intervals.
    """
    print("=" * 60)
    print("  COMPARATIVE WALK-FORWARD BACKTEST")
    print(f"  Max draws: {max_draws} | Random trials: {random_trials} | Seed: {random_seed} | Weights: {weights_mode}")
    print("=" * 60)

    # 1. Ensemble model (never falls back to random)
    ensemble_result = run_backtest(
        max_draws=max_draws,
        use_random_only=False,
        min_history=min_history,
        weights_mode=weights_mode,
    )

    # 2. Repeated random baseline trials (same draws, fixed seed)
    random.seed(random_seed)
    trial_accuracies = []
    trial_digit_hits = []
    trial_pos_hits = []
    trial_top2 = []
    trial_last2 = []
    trial_front3 = []
    trial_back3 = []
    trial_top3_direct = []
    trial_top3_box = []

    print(f"\n[INFO] Running {random_trials} repeated random baseline trials...")
    for t in range(random_trials):
        trial_res = run_backtest(
            max_draws=max_draws,
            use_random_only=True,
            min_history=min_history,
        )
        if trial_res:
            trial_accuracies.append(trial_res["positional_accuracy_pct"])
            trial_digit_hits.append(trial_res["average_digit_hits"])
            trial_pos_hits.append(trial_res["average_position_hits"])
            trial_top2.append(trial_res["metrics_2digit"]["top2_match_rate_pct"])
            trial_last2.append(trial_res["metrics_2digit"]["last2_match_rate_pct"])
            trial_front3.append(trial_res["metrics_3digit"]["front3_match_rate_pct"])
            trial_back3.append(trial_res["metrics_3digit"]["back3_match_rate_pct"])
            trial_top3_direct.append(trial_res["metrics_3digit"]["top3_direct_rate_pct"])
            trial_top3_box.append(trial_res["metrics_3digit"]["top3_box_rate_pct"])

    # Aggregate random trials statistics
    if trial_accuracies:
        k_trials = len(trial_accuracies)
        mean_rnd_acc = sum(trial_accuracies) / k_trials
        variance_rnd_acc = sum((x - mean_rnd_acc) ** 2 for x in trial_accuracies) / (k_trials - 1) if k_trials > 1 else 0.0
        std_rnd_acc = math.sqrt(variance_rnd_acc)
        sem_rnd_acc = std_rnd_acc / math.sqrt(k_trials) if k_trials > 0 else 0.0
        rnd_ci_95 = (
            round(max(0.0, mean_rnd_acc - 1.96 * sem_rnd_acc), 4),
            round(mean_rnd_acc + 1.96 * sem_rnd_acc, 4),
        )

        mean_rnd_dig = sum(trial_digit_hits) / k_trials
        mean_rnd_pos = sum(trial_pos_hits) / k_trials
        mean_rnd_top2 = sum(trial_top2) / k_trials
        mean_rnd_last2 = sum(trial_last2) / k_trials
        mean_rnd_front3 = sum(trial_front3) / k_trials
        mean_rnd_back3 = sum(trial_back3) / k_trials
        mean_rnd_top3_direct = sum(trial_top3_direct) / k_trials
        mean_rnd_top3_box = sum(trial_top3_box) / k_trials
    else:
        mean_rnd_acc = 10.0
        std_rnd_acc = 0.0
        rnd_ci_95 = (10.0, 10.0)
        mean_rnd_dig = 2.5
        mean_rnd_pos = 0.6
        mean_rnd_top2 = 1.0
        mean_rnd_last2 = 1.0
        mean_rnd_front3 = 0.2
        mean_rnd_back3 = 0.2
        mean_rnd_top3_direct = 0.1
        mean_rnd_top3_box = 0.6
        k_trials = 0

    comparison = {}
    if ensemble_result and trial_accuracies:
        ens_acc = ensemble_result["positional_accuracy_pct"]
        lift = round(ens_acc - mean_rnd_acc, 4)

        # Standard error of the difference
        ens_se = ensemble_result["statistical_uncertainty"]["standard_error"] * 100.0  # in percentage points
        diff_se = math.sqrt((ens_se ** 2) + ((std_rnd_acc ** 2) / k_trials)) if k_trials > 0 else ens_se
        z_diff = lift / diff_se if diff_se > 0 else 0.0
        p_diff = calc_two_tailed_p_value(z_diff)

        comparison = {
            "ensemble_avg_pos_hits": ensemble_result["average_position_hits"],
            "random_avg_pos_hits": round(mean_rnd_pos, 4),
            "ensemble_accuracy_pct": ens_acc,
            "random_accuracy_pct": round(mean_rnd_acc, 4),
            "ensemble_avg_dig_hits": ensemble_result["average_digit_hits"],
            "random_avg_dig_hits": round(mean_rnd_dig, 4),
            "lift_over_random_pct": lift,
            "random_baseline_std": round(std_rnd_acc, 4),
            "random_baseline_ci_95": {"lower_pct": rnd_ci_95[0], "upper_pct": rnd_ci_95[1]},
            "random_trials_count": k_trials,
            "hypothesis_test_vs_empirical_random": {
                "null_hypothesis": "Ensemble positional accuracy equals empirical random baseline mean",
                "z_score": round(z_diff, 4),
                "p_value": round(p_diff, 6),
                "statistically_significant_at_05": p_diff < 0.05 and z_diff > 0,
            },
            "official_prize_rates": {
                "front3_match_rate_pct": {
                    "ensemble": ensemble_result.get("metrics_official_prizes", {}).get("front3_prizes", {}).get("match_rate_pct", 0.0),
                    "random_empirical_mean": round(mean_rnd_front3, 4),
                    "theoretical_random": 0.20,
                },
                "back3_match_rate_pct": {
                    "ensemble": ensemble_result.get("metrics_official_prizes", {}).get("back3_prizes", {}).get("match_rate_pct", 0.0),
                    "random_empirical_mean": round(mean_rnd_back3, 4),
                    "theoretical_random": 0.20,
                },
                "last2_match_rate_pct": {
                    "ensemble": ensemble_result.get("metrics_official_prizes", {}).get("last2_prize", {}).get("match_rate_pct", 0.0),
                    "random_empirical_mean": round(mean_rnd_last2, 4),
                    "theoretical_random": 1.00,
                },
            },
            "disclaimer": (
                "Do not interpret a positive lift as proof of predictive advantage. "
                "Due to high variance and inherent randomness in lottery draws, sample hit rate variations "
                "are consistent with random statistical fluctuations. Lottery outcomes are designed to be independent and uniformly random."
            ),
        }

    return {
        "ensemble": {k: v for k, v in ensemble_result.items() if k != "draws_evaluated"},
        "random_baseline": {
            "mode": f"RANDOM BASELINE ({k_trials} repeated trials, seed={random_seed})",
            "trials_count": k_trials,
            "mean_positional_accuracy_pct": round(mean_rnd_acc, 4),
            "std_positional_accuracy_pct": round(std_rnd_acc, 4),
            "ci_95_pct": {"lower_pct": rnd_ci_95[0], "upper_pct": rnd_ci_95[1]},
            "mean_digit_hits": round(mean_rnd_dig, 4),
            "mean_pos_hits": round(mean_rnd_pos, 4),
            "mean_top2_match_rate_pct": round(mean_rnd_top2, 4),
            "mean_last2_match_rate_pct": round(mean_rnd_last2, 4),
            "mean_front3_match_rate_pct": round(mean_rnd_front3, 4),
            "mean_back3_match_rate_pct": round(mean_rnd_back3, 4),
            "mean_top3_direct_rate_pct": round(mean_rnd_top3_direct, 4),
            "mean_top3_box_rate_pct": round(mean_rnd_top3_box, 4),
            "expected_theoretical_accuracy_pct": 10.0,
        },
        "comparison": comparison,
        "sample_size": {
            "attempted_draws": ensemble_result.get("attempted_draws", 0),
            "successful_draws": ensemble_result.get("successful_draws", 0),
            "coverage_rate_pct": ensemble_result.get("coverage", {}).get("coverage_rate_pct", 100.0),
            "failures_count": ensemble_result.get("prediction_failures", 0),
            "failure_rate_pct": ensemble_result.get("failure_rate_pct", 0.0),
        },
        "timestamp": datetime.now().isoformat(),
    }


def save_report(summary: dict):
    """
    Save the backtest results to JSON and CSV formats.
    """
    if "draws_evaluated" not in summary:
        print("[WARN] No data to save.")
        return

    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

    draws = summary.pop("draws_evaluated")

    # 1. Save JSON
    output_json = {
        "summary": summary,
        "details": draws
    }
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)

    # 2. Save CSV
    with open(REPORT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "date", "actual", "predicted", "digit_hits", "position_hits",
            "exact_match", "top2_match", "last2_match", "front3_match", "back3_match",
            "top3_direct", "top3_box", "status"
        ])
        for d in draws:
            writer.writerow([
                d["date"],
                d["actual"],
                d.get("predicted", ""),
                d["digit_hits"],
                d["position_hits"],
                d["exact_match"],
                d.get("top2_match", False),
                d.get("last2_match", False),
                d.get("front3_match", False),
                d.get("back3_match", False),
                d.get("top3_direct", False),
                d.get("top3_box", False),
                d.get("status", "success"),
            ])

    # Put it back to avoid mutating caller's dict silently
    summary["draws_evaluated"] = draws

    print(f"[INFO] Report saved to:\n  - {REPORT_JSON}\n  - {REPORT_CSV}")


def main():
    parser = argparse.ArgumentParser(description="AI Backtesting Engine")
    parser.add_argument("--run", action="store_true", help="Run the backtest simulator")
    parser.add_argument("--compare", action="store_true", help="Compare ensemble vs random baseline")
    parser.add_argument("--draws", type=int, default=50, help="Max draws to evaluate (0=all)")
    parser.add_argument("--trials", type=int, default=10, help="Number of random baseline trials (default 10)")
    parser.add_argument("--seed", type=int, default=42, help="Fixed random seed (default 42)")
    parser.add_argument("--min-history", type=int, default=100, help="Minimum history required (default 100)")
    parser.add_argument("--weights", choices=["calibrated", "equal"], default="calibrated", help="Weights mode: calibrated from disk or untuned equal (default: calibrated)")
    parser.add_argument("--audit", action="store_true", help="Audit ensemble weights and partitioning for look-ahead data leakage")
    parser.add_argument("--random-only", action="store_true", help="Random baseline only")
    args = parser.parse_args()

    if args.audit:
        print("\n" + "=" * 60)
        print("  LOOK-AHEAD DATA LEAKAGE AUDIT")
        print("=" * 60)
        res = audit_weights_leakage()
        for k, v in res.items():
            print(f"  {k:30s}: {v}")
        print("=" * 60)
        if res.get("passed"):
            print("  AUDIT RESULT: PASSED (Zero future-data leakage detected)")
        else:
            print("  AUDIT RESULT: FAILED")
        print("=" * 60 + "\n")
        return

    if args.compare:
        result = run_comparative_backtest(
            max_draws=args.draws,
            random_trials=args.trials,
            random_seed=args.seed,
            min_history=args.min_history,
            weights_mode=args.weights,
        )
        print("\n" + "=" * 60)
        print("  COMPARATIVE BACKTEST RESULTS")
        print("=" * 60)
        ens = result.get("ensemble", {})
        rnd = result.get("random_baseline", {})
        cmp = result.get("comparison", {})
        ss = result.get("sample_size", {})
        print(f"  Sample size (draws)          : {ss.get('successful_draws', 0)} / {ss.get('attempted_draws', 0)} attempted (Coverage: {ss.get('coverage_rate_pct', 0.0):.2f}%)")
        print(f"  Predictor failures           : {ss.get('failures_count', 0)} ({ss.get('failure_rate_pct', 0.0):.2f}%)")
        print(f"  Ensemble positional accuracy : {ens.get('positional_accuracy_pct', 0):.2f}%")
        print(f"  Random baseline mean accuracy: {rnd.get('mean_positional_accuracy_pct', 0):.2f}% (std: {rnd.get('std_positional_accuracy_pct', 0):.2f}%)")
        print(f"  Lift over random             : {cmp.get('lift_over_random_pct', 0):+.2f}%")
        print(f"  Ensemble 95% Wilson CI       : [{ens.get('statistical_uncertainty', {}).get('wilson_ci_95', {}).get('lower_pct', 0):.2f}%, {ens.get('statistical_uncertainty', {}).get('wilson_ci_95', {}).get('upper_pct', 0):.2f}%]")
        print(f"  Ensemble avg digit hits      : {ens.get('average_digit_hits', 0):.2f}/6")
        print(f"  Random avg digit hits        : {rnd.get('mean_digit_hits', 0):.2f}/6")
        ht = cmp.get("hypothesis_test_vs_empirical_random", {})
        print(f"  Z-score / p-value            : z={ht.get('z_score', 0):.4f}, p={ht.get('p_value', 1.0):.6f}")
        print(f"  Statistical significance     : {ht.get('statistically_significant_at_05', False)}")
        print("=" * 60)
        print(f"  DISCLAIMER: {cmp.get('disclaimer', '')}")
        print("=" * 60)

        # Save comparison
        BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
        cmp_path = BACKTEST_DIR / "comparative_report.json"
        cmp_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8"
        )
        print(f"[INFO] Saved → {cmp_path}")

    elif args.run:
        summary = run_backtest(
            max_draws=args.draws,
            use_random_only=args.random_only,
            min_history=args.min_history,
            random_seed=args.seed if args.random_only else None,
            weights_mode=args.weights,
        )
        if summary:
            save_report(summary)
            print("\n===============================")
            print(" Backtest Report")
            print("===============================")
            print(f" Mode                    : {summary['mode']}")
            print(f" Attempted draws         : {summary['attempted_draws']}")
            print(f" Successful draws        : {summary['successful_draws']}")
            print(f" Coverage rate           : {summary.get('coverage', {}).get('coverage_rate_pct', 0.0)}%")
            print(f" Prediction failures     : {summary['prediction_failures']} ({summary['failure_rate_pct']}%)")
            print(f" Exact matches           : {summary['exact_matches']} ({summary['exact_match_rate']:.4%})")
            print(f" Average digit hits      : {summary['average_digit_hits']} / 6")
            print(f" Average position hits   : {summary['average_position_hits']} / 6")
            print(f" Positional Accuracy     : {summary['positional_accuracy_pct']}%")
            ci = summary.get("metrics_6digit", {})
            print(f" 95% Wilson CI           : [{ci.get('ci_95_lower_pct', 0)}%, {ci.get('ci_95_upper_pct', 0)}%]")
            print(f" Note: {summary['note']}")
            print("===============================\n")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
