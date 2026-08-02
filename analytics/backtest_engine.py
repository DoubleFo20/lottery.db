"""
Lottery AI Backtesting Engine
=============================
Evaluates AI strategy performance on historical lottery draws.
"""

import argparse
import csv
import json
import random
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
BACKTEST_DIR = BASE_DIR / "database" / "backtest"
REPORT_JSON = BACKTEST_DIR / "backtest_report.json"
REPORT_CSV = BACKTEST_DIR / "backtest_report.csv"


def load_history() -> list[dict]:
    """Load historical lottery draws from CSV."""
    history = []
    if not CSV_PATH.exists():
        print(f"[ERROR] Dataset not found: {CSV_PATH}")
        return history

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_val = row.get("draw_date", "")
            # Reconstruct the 6-digit winning number
            digits = []
            for i in range(1, 7):
                d = row.get(f"digit{i}", "")
                digits.append(d)
            number = "".join(digits)
            if date_val and len(number) == 6:
                history.append({"date": date_val, "number": number})
    
    # Sort chronologically
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

    # Calculate digit_hits (shared digits)
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


def _simulate_prediction(date: str, history_up_to_date: list) -> str:
    """
    Generate a prediction for the given date, using historical data prior to it.
    *(Placeholder for the real AI model. Currently returns a random 6-digit number)*
    """
    # TODO: Connect real predictor here, e.g., EnsemblePredictor
    return f"{random.randint(0, 999999):06d}"


def run_backtest() -> dict:
    """
    Iterate over history and evaluate prediction system performance.
    """
    history = load_history()
    if not history:
        print("[WARN] Empty history. Cannot run backtest.")
        return {}

    print(f"\n[INFO] Running backtest on {len(history)} draws...")
    results = []
    total_draws = 0
    exact_matches = 0
    total_digit_hits = 0
    total_pos_hits = 0

    # Backtest loop
    # We skip early draws to have enough history for the predictor
    min_history_required = 100
    
    for i, draw in enumerate(history):
        if i < min_history_required:
            continue
            
        history_up_to_date = history[:i]
        actual_number = draw["number"]
        draw_date = draw["date"]

        # Call prediction model
        predicted_number = _simulate_prediction(draw_date, history_up_to_date)

        # Score it
        score = score_prediction(predicted_number, actual_number)
        score["date"] = draw_date
        results.append(score)

        # Track metrics
        total_draws += 1
        if score["exact_match"]:
            exact_matches += 1
        total_digit_hits += score["digit_hits"]
        total_pos_hits += score["position_hits"]

    if total_draws == 0:
        return {}

    # Produce summary metrics
    summary = {
        "total_draws": total_draws,
        "exact_matches": exact_matches,
        "exact_match_rate": round(exact_matches / total_draws, 4),
        "average_digit_hits": round(total_digit_hits / total_draws, 2),
        "average_position_hits": round(total_pos_hits / total_draws, 2),
        "accuracy_score": round((total_pos_hits / 6) * 100, 2), # Base score on positional hitting
        "run_time": datetime.now().isoformat(),
        "draws_evaluated": results
    }

    return summary


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
    # We keep the summary separated from the massive draws list inside the JSON for cleanliness
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
    args = parser.parse_args()

    if args.run:
        summary = run_backtest()
        if summary:
            save_report(summary)
            print("\n===============================")
            print(" Backtest Report")
            print("===============================")
            print(f" Total draws tested      : {summary['total_draws']}")
            print(f" Exact matches           : {summary['exact_matches']} ({summary['exact_match_rate']:.2%})")
            print(f" Average digit hits      : {summary['average_digit_hits']} / 6")
            print(f" Average position hits   : {summary['average_position_hits']} / 6")
            print(f" Positional Accuracy     : {summary['accuracy_score']}%")
            print("===============================\n")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
