"""
Self-Learning Module
=====================
Evaluates prediction accuracy against actual lottery results and
auto-adjusts ensemble model weights to improve future predictions.

Input:
  - Prediction history (JSON log)
  - Actual results     (lottery_history.csv)

Tasks:
  1. Log predictions with timestamps
  2. Evaluate accuracy (exact match, positional match, digit hit rate)
  3. Adjust ensemble weights via gradient-free optimisation
  4. Persist updated weights for the ensemble predictor

Storage:
  database/predictions/prediction_log.json   — prediction history
  database/predictions/weight_history.json   — weight evolution log
  database/predictions/accuracy_report.json  — latest accuracy report

Usage:
  python ai_engine/self_learning.py --log                # log current prediction
  python ai_engine/self_learning.py --evaluate           # evaluate all predictions
  python ai_engine/self_learning.py --adapt              # adjust weights
  python ai_engine/self_learning.py --report             # full accuracy report
  python ai_engine/self_learning.py --auto               # log + evaluate + adapt
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR        = Path(__file__).resolve().parents[1]
CSV_PATH        = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
PRED_DIR        = BASE_DIR / "database" / "predictions"
PRED_LOG        = PRED_DIR / "prediction_log.json"
WEIGHT_LOG      = PRED_DIR / "weight_history.json"
ACCURACY_REPORT = PRED_DIR / "accuracy_report.json"
WEIGHT_FILE     = PRED_DIR / "ensemble_weights.json"

DIGIT_COLS = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]

# Default ensemble weights (mirrors ensemble_model/predictor.py)
DEFAULT_WEIGHTS = {
    "positional_freq":  0.20,
    "rolling_heat":     0.20,
    "conditional":      0.15,
    "transition":       0.10,
    "pair_lift":        0.10,
    "pattern_hot":      0.10,
    "gap_overdue":      0.08,
    "temporal_trend":   0.07,
}

LEARNING_RATE    = 0.02    # step size per adaptation
MIN_WEIGHT       = 0.02   # floor — prevent any signal from going to 0
MAX_WEIGHT       = 0.40   # ceiling — prevent over-reliance on one signal


# ═══════════════════════════════════════════════════════════════════════════
#  Utility
# ═══════════════════════════════════════════════════════════════════════════

def _load_json(path: Path) -> list | dict:
    if path.exists() and path.stat().st_size > 0:
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8")


def _load_actual_results() -> dict[str, dict]:
    """Load CSV into dict keyed by draw_date."""
    results = {}
    if CSV_PATH.exists():
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                d = row.get("draw_date", "").strip()
                if d:
                    results[d] = row
    return results


def _load_weights() -> dict[str, float]:
    """Load current weights from file, or return defaults."""
    if WEIGHT_FILE.exists():
        try:
            return json.loads(WEIGHT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(DEFAULT_WEIGHTS)


def _save_weights(weights: dict[str, float]) -> None:
    _save_json(WEIGHT_FILE, weights)


# ═══════════════════════════════════════════════════════════════════════════
#  1. Log Prediction
# ═══════════════════════════════════════════════════════════════════════════

def log_prediction(candidates: list[dict] | None = None,
                   target_date: str = "") -> None:
    """
    Log the current ensemble prediction. If candidates is None,
    run the predictor to generate them.
    """
    if candidates is None:
        # Import and run predictor
        sys.path.insert(0, str(BASE_DIR))
        from ensemble_model.predictor import EnsemblePredictor
        predictor = EnsemblePredictor(CSV_PATH)
        candidates = predictor.run(top_k=5, beam_width=3)

    log_data = _load_json(PRED_LOG)
    if not isinstance(log_data, list):
        log_data = []

    entry = {
        "predicted_at": datetime.now().isoformat(),
        "target_date":  target_date,
        "candidates":   candidates,
        "weights_used": _load_weights(),
    }

    log_data.append(entry)
    _save_json(PRED_LOG, log_data)
    print(f"[INFO] Logged {len(candidates)} candidates (total entries: {len(log_data)})")


# ═══════════════════════════════════════════════════════════════════════════
#  2. Evaluate Accuracy
# ═══════════════════════════════════════════════════════════════════════════

def _score_prediction(predicted: str, actual: str) -> dict:
    """
    Score a single 6-digit prediction against actual result.

    Metrics:
      exact_match:    True if predicted == actual
      positional_hits: count of positions where digit matches exactly
      digit_hits:      count of predicted digits found anywhere in actual
      digit_hit_rate:  digit_hits / 6
      positional_rate: positional_hits / 6
    """
    p = list(predicted.ljust(6, "0")[:6])
    a = list(actual.ljust(6, "0")[:6])

    positional = sum(1 for i in range(6) if p[i] == a[i])
    # Digit hits — each predicted digit matched once at most
    a_pool = list(a)
    digit_hits = 0
    for d in p:
        if d in a_pool:
            digit_hits += 1
            a_pool.remove(d)

    return {
        "exact_match":     predicted == actual,
        "positional_hits": positional,
        "positional_rate": round(positional / 6, 4),
        "digit_hits":      digit_hits,
        "digit_hit_rate":  round(digit_hits / 6, 4),
    }


def evaluate_predictions() -> dict:
    """
    Match logged predictions against actual results and compute
    aggregate accuracy metrics.
    """
    log_data = _load_json(PRED_LOG)
    if not isinstance(log_data, list) or not log_data:
        print("[WARN] No predictions logged yet")
        return {"error": "No predictions logged"}

    actuals = _load_actual_results()
    evaluated = []
    total_pos_hits = 0
    total_digit_hits = 0
    total_candidates = 0
    exact_matches = 0

    for entry in log_data:
        target = entry.get("target_date", "")
        candidates = entry.get("candidates", [])

        if not target or target not in actuals:
            entry["evaluation"] = {"status": "pending", "reason": "no actual result yet"}
            evaluated.append(entry)
            continue

        actual_row = actuals[target]
        actual_number = "".join(actual_row.get(c, "") for c in DIGIT_COLS)

        best_score = None
        cand_evals = []

        for cand in candidates:
            num = cand.get("number", "")
            sc = _score_prediction(num, actual_number)
            sc["candidate"] = num
            cand_evals.append(sc)

            if best_score is None or sc["positional_hits"] > best_score["positional_hits"]:
                best_score = sc

            total_pos_hits += sc["positional_hits"]
            total_digit_hits += sc["digit_hits"]
            total_candidates += 1
            if sc["exact_match"]:
                exact_matches += 1

        entry["evaluation"] = {
            "status": "evaluated",
            "actual_number": actual_number,
            "actual_date": target,
            "candidate_scores": cand_evals,
            "best_candidate": best_score,
        }
        evaluated.append(entry)

    # Aggregate
    avg_pos = total_pos_hits / total_candidates if total_candidates else 0
    avg_digit = total_digit_hits / total_candidates if total_candidates else 0

    report = {
        "total_predictions":   len(log_data),
        "evaluated":           sum(1 for e in evaluated if e.get("evaluation", {}).get("status") == "evaluated"),
        "pending":             sum(1 for e in evaluated if e.get("evaluation", {}).get("status") == "pending"),
        "total_candidates":    total_candidates,
        "exact_matches":       exact_matches,
        "avg_positional_hits": round(avg_pos, 4),
        "avg_positional_rate": round(avg_pos / 6, 4) if total_candidates else 0,
        "avg_digit_hits":      round(avg_digit, 4),
        "avg_digit_hit_rate":  round(avg_digit / 6, 4) if total_candidates else 0,
        "evaluated_at":        datetime.now().isoformat(),
        "entries":             evaluated,
    }

    _save_json(ACCURACY_REPORT, report)
    _save_json(PRED_LOG, evaluated)  # update log with evaluation data

    print(f"[INFO] Evaluated {report['evaluated']}/{report['total_predictions']} predictions")
    print(f"[INFO] Avg positional hits: {avg_pos:.2f}/6  |  Avg digit hits: {avg_digit:.2f}/6")
    return report


# ═══════════════════════════════════════════════════════════════════════════
#  3. Adapt Weights (Self-Learning)
# ═══════════════════════════════════════════════════════════════════════════

def _compute_signal_contribution(entry: dict) -> dict[str, float]:
    """
    Estimate each signal's contribution to accuracy for a single prediction.
    Uses the weights that were active and the resulting positional accuracy.
    """
    weights_used = entry.get("weights_used", DEFAULT_WEIGHTS)
    evaluation = entry.get("evaluation", {})
    best = evaluation.get("best_candidate", {})

    if not best or evaluation.get("status") != "evaluated":
        return {}

    pos_rate = best.get("positional_rate", 0)
    digit_rate = best.get("digit_hit_rate", 0)
    combined_score = 0.6 * pos_rate + 0.4 * digit_rate  # blend

    # Attribution: reward signals proportional to their weight × accuracy
    contributions = {}
    for signal, weight in weights_used.items():
        contributions[signal] = weight * combined_score

    return contributions


def adapt_weights() -> dict[str, float]:
    """
    Adjust ensemble weights based on accumulated prediction accuracy.

    Strategy:
      - For each evaluated prediction, compute per-signal contribution
      - Signals associated with higher accuracy get weight increases
      - Signals with poor accuracy get weight decreases
      - Apply learning rate and clamp to [MIN_WEIGHT, MAX_WEIGHT]
      - Normalise so weights sum to 1.0
    """
    log_data = _load_json(PRED_LOG)
    current_weights = _load_weights()

    if not isinstance(log_data, list) or not log_data:
        print("[WARN] No prediction data — nothing to learn from")
        return current_weights

    # Gather evaluated entries
    evaluated = [e for e in log_data
                 if e.get("evaluation", {}).get("status") == "evaluated"]

    if not evaluated:
        print("[WARN] No evaluated predictions — run --evaluate first")
        return current_weights

    # Compute average contribution per signal across all evaluations
    signal_scores: dict[str, list[float]] = defaultdict(list)
    for entry in evaluated:
        contribs = _compute_signal_contribution(entry)
        for signal, score in contribs.items():
            signal_scores[signal].append(score)

    avg_scores = {s: sum(v) / len(v) for s, v in signal_scores.items() if v}

    if not avg_scores:
        return current_weights

    # Compute gradient: difference from mean performance
    mean_score = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0

    new_weights = deepcopy(current_weights)
    for signal in new_weights:
        if signal in avg_scores:
            delta = avg_scores[signal] - mean_score
            # Positive delta → signal helped → increase weight
            new_weights[signal] += LEARNING_RATE * delta
            # Clamp
            new_weights[signal] = max(MIN_WEIGHT, min(MAX_WEIGHT, new_weights[signal]))

    # Normalise to sum = 1.0
    total = sum(new_weights.values())
    if total > 0:
        new_weights = {k: round(v / total, 5) for k, v in new_weights.items()}

    # Save
    _save_weights(new_weights)

    # Log weight change
    weight_history = _load_json(WEIGHT_LOG)
    if not isinstance(weight_history, list):
        weight_history = []
    weight_history.append({
        "adapted_at":     datetime.now().isoformat(),
        "old_weights":    current_weights,
        "new_weights":    new_weights,
        "evaluated_count": len(evaluated),
        "avg_scores":     avg_scores,
    })
    _save_json(WEIGHT_LOG, weight_history)

    # Show changes
    print("\n─── WEIGHT ADAPTATION ───────────────────────")
    print(f"  {'Signal':<20} {'Old':>7} {'New':>7} {'Δ':>7}")
    print(f"  {'─'*20} {'─'*7} {'─'*7} {'─'*7}")
    for signal in sorted(new_weights):
        old = current_weights.get(signal, 0)
        new = new_weights[signal]
        delta = new - old
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "=")
        print(f"  {signal:<20} {old:>6.1%} {new:>6.1%} {delta:>+6.1%} {arrow}")
    print(f"\n[INFO] Weights adapted and saved ({len(evaluated)} evaluations)")
    return new_weights


# ═══════════════════════════════════════════════════════════════════════════
#  4. Print Report
# ═══════════════════════════════════════════════════════════════════════════

def print_report() -> None:
    """Print a human-readable accuracy report."""
    report = _load_json(ACCURACY_REPORT)
    if not report or isinstance(report, list):
        print("[WARN] No accuracy report — run --evaluate first")
        return

    print("\n" + "=" * 62)
    print("  📊 SELF-LEARNING ACCURACY REPORT")
    print("=" * 62)
    print(f"  Total predictions : {report.get('total_predictions', 0)}")
    print(f"  Evaluated         : {report.get('evaluated', 0)}")
    print(f"  Pending           : {report.get('pending', 0)}")
    print(f"  Exact matches     : {report.get('exact_matches', 0)}")
    print(f"  Avg pos hits      : {report.get('avg_positional_hits', 0):.2f} / 6  "
          f"({report.get('avg_positional_rate', 0):.1%})")
    print(f"  Avg digit hits    : {report.get('avg_digit_hits', 0):.2f} / 6  "
          f"({report.get('avg_digit_hit_rate', 0):.1%})")

    # Per-entry breakdown
    entries = report.get("entries", [])
    evaluated = [e for e in entries if e.get("evaluation", {}).get("status") == "evaluated"]

    if evaluated:
        print(f"\n─── EVALUATED PREDICTIONS ───────────────────")
        for entry in evaluated[-10:]:  # last 10
            ev = entry["evaluation"]
            best = ev.get("best_candidate", {})
            print(f"  {ev.get('actual_date', '?')}: actual={ev.get('actual_number', '?')}  "
                  f"best={best.get('candidate', '?')}  "
                  f"pos={best.get('positional_hits', 0)}/6  "
                  f"dig={best.get('digit_hits', 0)}/6")

    # Current weights
    weights = _load_weights()
    print(f"\n─── CURRENT ENSEMBLE WEIGHTS ────────────────")
    for signal, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(w * 50)
        print(f"  {signal:<20} {w:>6.1%}  {bar}")

    print("\n" + "=" * 62)


# ═══════════════════════════════════════════════════════════════════════════
#  Auto pipeline
# ═══════════════════════════════════════════════════════════════════════════

def auto_pipeline() -> None:
    """Full self-learning cycle: log → evaluate → adapt → report."""
    print("[AUTO] Step 1/4: Logging current prediction…")
    log_prediction()

    print("\n[AUTO] Step 2/4: Evaluating predictions…")
    evaluate_predictions()

    print("\n[AUTO] Step 3/4: Adapting weights…")
    adapt_weights()

    print("\n[AUTO] Step 4/4: Generating report…")
    print_report()


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Lottery Self-Learning Module")
    parser.add_argument("--log",      action="store_true", help="Log current prediction")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate predictions vs actuals")
    parser.add_argument("--adapt",    action="store_true", help="Adjust ensemble weights")
    parser.add_argument("--report",   action="store_true", help="Print accuracy report")
    parser.add_argument("--auto",     action="store_true", help="Full pipeline: log→evaluate→adapt→report")
    parser.add_argument("--target",   type=str, default="", help="Target draw date for logging (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.auto:
        auto_pipeline()
    elif args.log:
        log_prediction(target_date=args.target)
    elif args.evaluate:
        evaluate_predictions()
    elif args.adapt:
        adapt_weights()
    elif args.report:
        print_report()
    else:
        # Default: show report if exists, else run auto
        if ACCURACY_REPORT.exists():
            print_report()
        else:
            print("[INFO] No report found — running auto pipeline…")
            auto_pipeline()


if __name__ == "__main__":
    main()
