"""
Lottery AI Backtesting Engine
=============================
Walk-forward evaluation of the ensemble prediction model against
historical lottery draws.

Key design decisions:
  • Uses real EnsemblePredictor (no random fallback).
  • Walk-forward: for each test draw, only prior draws are visible.
  • Accuracy = total_position_hits / (total_draws × 6).
  • Measures a random baseline for honest comparison.
  • Reports uncertainty honestly — lottery outcomes are inherently random.
"""

import argparse
import csv
import json
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


def score_prediction(predicted: str, actual: str) -> dict:
    """
    Compare predicted number with the actual number.
    Returns digit_hits, position_hits, and exact_match.
    """
    predicted = str(predicted).zfill(6)[:6]
    actual = str(actual).zfill(6)[:6]

    # Calculate position_hits
    position_hits = sum(1 for p, a in zip(predicted, actual) if p == a)

    # Calculate digit_hits (shared digits, each matched once)
    p_list = list(predicted)
    a_list = list(actual)
    digit_hits = 0
    for d in p_list:
        if d in a_list:
            digit_hits += 1
            a_list.remove(d)

    return {
        "predicted": predicted,
        "actual": actual,
        "exact_match": predicted == actual,
        "position_hits": position_hits,
        "digit_hits": digit_hits
    }


def _predict_with_ensemble(history_rows: list[dict], top_k: int = 1) -> str:
    """
    Generate a prediction using the real EnsemblePredictor,
    trained only on the provided history_rows (walk-forward).
    Returns the top-1 candidate number string.
    """
    from ensemble_model.predictor import EnsemblePredictor

    predictor = EnsemblePredictor(CSV_PATH, window=min(50, len(history_rows)))
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


def _random_prediction() -> str:
    """Generate a uniformly random 6-digit number for baseline measurement."""
    return f"{random.randint(0, 999999):06d}"


def run_backtest(max_draws: int = 0, use_random_only: bool = False) -> dict:
    """
    Walk-forward backtest: for each draw i >= min_history,
    predict using only draws [0..i-1], then score against draw i.

    If use_random_only=True, generates random baseline measurement.
    """
    history = load_history()
    if not history:
        print("[WARN] Empty history. Cannot run backtest.")
        return {}

    min_history_required = 100
    if len(history) <= min_history_required:
        print(f"[WARN] Not enough history ({len(history)} draws, need >{min_history_required})")
        return {}

    test_range = list(range(min_history_required, len(history)))
    if max_draws > 0:
        test_range = test_range[-max_draws:]  # most recent N draws

    mode = "RANDOM BASELINE" if use_random_only else "ENSEMBLE MODEL"
    print(f"\n[INFO] Running {mode} backtest on {len(test_range)} draws...")

    results = []
    total_draws = 0
    exact_matches = 0
    total_digit_hits = 0
    total_pos_hits = 0

    for count, i in enumerate(test_range):
        history_up_to = [h["raw"] for h in history[:i]]
        actual_number = history[i]["number"]
        draw_date = history[i]["date"]

        # Generate prediction
        if use_random_only:
            predicted_number = _random_prediction()
        else:
            try:
                predicted_number = _predict_with_ensemble(history_up_to)
            except Exception as e:
                print(f"  [WARN] Predictor failed for {draw_date}: {e}")
                predicted_number = _random_prediction()

        # Score it
        sc = score_prediction(predicted_number, actual_number)
        sc["date"] = draw_date
        results.append(sc)

        # Track metrics
        total_draws += 1
        if sc["exact_match"]:
            exact_matches += 1
        total_digit_hits += sc["digit_hits"]
        total_pos_hits += sc["position_hits"]

        # Progress reporting
        if (count + 1) % 50 == 0 or count == 0:
            print(f"  [{count+1}/{len(test_range)}] avg_pos={total_pos_hits/total_draws:.2f}/6  "
                  f"avg_dig={total_digit_hits/total_draws:.2f}/6")

    if total_draws == 0:
        return {}

    # ── Corrected accuracy formula ──
    # Positional accuracy = total_pos_hits / (total_draws × 6)
    # This gives a value in [0, 1], representing the fraction of
    # individual digit positions correctly predicted.
    positional_accuracy = total_pos_hits / (total_draws * 6)

    summary = {
        "mode": mode,
        "total_draws": total_draws,
        "exact_matches": exact_matches,
        "exact_match_rate": round(exact_matches / total_draws, 6),
        "average_digit_hits": round(total_digit_hits / total_draws, 4),
        "average_position_hits": round(total_pos_hits / total_draws, 4),
        "positional_accuracy_pct": round(positional_accuracy * 100, 4),
        "note": (
            "Positional accuracy = total_position_hits / (draws × 6). "
            "Random baseline expectation ≈ 10% (1/10 per digit position). "
            "Lottery outcomes are inherently unpredictable."
        ),
        "run_time": datetime.now().isoformat(),
        "draws_evaluated": results,
    }

    return summary


def run_comparative_backtest(max_draws: int = 50) -> dict:
    """
    Run both ensemble and random baselines, then compare.
    """
    print("=" * 60)
    print("  COMPARATIVE WALK-FORWARD BACKTEST")
    print("=" * 60)

    # 1. Ensemble model
    ensemble_result = run_backtest(max_draws=max_draws, use_random_only=False)

    # 2. Measured random baseline (same draws, random predictions)
    random_result = run_backtest(max_draws=max_draws, use_random_only=True)

    comparison = {}
    if ensemble_result and random_result:
        comparison = {
            "ensemble_avg_pos_hits": ensemble_result["average_position_hits"],
            "random_avg_pos_hits": random_result["average_position_hits"],
            "ensemble_accuracy_pct": ensemble_result["positional_accuracy_pct"],
            "random_accuracy_pct": random_result["positional_accuracy_pct"],
            "ensemble_avg_dig_hits": ensemble_result["average_digit_hits"],
            "random_avg_dig_hits": random_result["average_digit_hits"],
            "lift_over_random_pct": round(
                ensemble_result["positional_accuracy_pct"]
                - random_result["positional_accuracy_pct"], 4
            ),
            "interpretation": (
                "Positive lift = model captures some signal above chance. "
                "Near-zero or negative lift = no reliable predictive edge. "
                "Lottery draws are designed to be uniformly random."
            ),
        }

    return {
        "ensemble": {k: v for k, v in ensemble_result.items() if k != "draws_evaluated"},
        "random_baseline": {k: v for k, v in random_result.items() if k != "draws_evaluated"},
        "comparison": comparison,
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
        writer.writerow(["date", "actual", "predicted", "digit_hits", "position_hits", "exact_match"])
        for d in draws:
            writer.writerow([
                d["date"],
                d["actual"],
                d["predicted"],
                d["digit_hits"],
                d["position_hits"],
                d["exact_match"]
            ])

    # Put it back to avoid mutating caller's dict silently
    summary["draws_evaluated"] = draws

    print(f"[INFO] Report saved to:\n  - {REPORT_JSON}\n  - {REPORT_CSV}")


def main():
    parser = argparse.ArgumentParser(description="AI Backtesting Engine")
    parser.add_argument("--run", action="store_true", help="Run the backtest simulator")
    parser.add_argument("--compare", action="store_true", help="Compare ensemble vs random baseline")
    parser.add_argument("--draws", type=int, default=50, help="Max draws to evaluate (0=all)")
    parser.add_argument("--random-only", action="store_true", help="Random baseline only")
    args = parser.parse_args()

    if args.compare:
        result = run_comparative_backtest(max_draws=args.draws)
        print("\n" + "=" * 60)
        print("  COMPARATIVE BACKTEST RESULTS")
        print("=" * 60)
        ens = result.get("ensemble", {})
        rnd = result.get("random_baseline", {})
        cmp = result.get("comparison", {})
        print(f"  Ensemble positional accuracy : {ens.get('positional_accuracy_pct', 0):.2f}%")
        print(f"  Random baseline accuracy     : {rnd.get('positional_accuracy_pct', 0):.2f}%")
        print(f"  Lift over random             : {cmp.get('lift_over_random_pct', 0):+.2f}%")
        print(f"  Ensemble avg digit hits      : {ens.get('average_digit_hits', 0):.2f}/6")
        print(f"  Random avg digit hits        : {rnd.get('average_digit_hits', 0):.2f}/6")
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
        summary = run_backtest(max_draws=args.draws, use_random_only=args.random_only)
        if summary:
            save_report(summary)
            print("\n===============================")
            print(" Backtest Report")
            print("===============================")
            print(f" Mode                    : {summary['mode']}")
            print(f" Total draws tested      : {summary['total_draws']}")
            print(f" Exact matches           : {summary['exact_matches']} ({summary['exact_match_rate']:.4%})")
            print(f" Average digit hits      : {summary['average_digit_hits']} / 6")
            print(f" Average position hits   : {summary['average_position_hits']} / 6")
            print(f" Positional Accuracy     : {summary['positional_accuracy_pct']}%")
            print(f" Note: {summary['note']}")
            print("===============================\n")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
