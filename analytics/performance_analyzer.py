"""
Performance Analyzer
=====================
Evaluates the AI prediction system's performance over time.

Input:
  database/predictions/prediction_history.json   (from prediction_history.py)

Metrics:
  1. Hit Rate         — % of predictions that matched ≥ N digits
  2. Digit Accuracy   — per-position and per-digit accuracy rates
  3. Model Score      — composite weighted score of all metrics

Usage:
  python analytics/performance_analyzer.py                  # full report
  python analytics/performance_analyzer.py --json           # JSON output
  python analytics/performance_analyzer.py --save perf.json
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
BASE_DIR     = Path(__file__).resolve().parents[1]
HISTORY_JSON = BASE_DIR / "database" / "predictions" / "prediction_history.json"
DIGIT_COLS   = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]


# ═══════════════════════════════════════════════════════════════════════════
#  Data Loading
# ═══════════════════════════════════════════════════════════════════════════

def _load_history() -> list[dict]:
    if not HISTORY_JSON.exists():
        return []
    data = json.loads(HISTORY_JSON.read_text(encoding="utf-8"))
    return [e for e in data if e.get("accuracy")]  # only evaluated entries


# ═══════════════════════════════════════════════════════════════════════════
#  1. Hit Rate Analysis
# ═══════════════════════════════════════════════════════════════════════════

def compute_hit_rate(entries: list[dict]) -> dict:
    """
    For each threshold (1–6 positional hits), compute what % of
    predictions had at least that many positional hits in its
    best candidate.
    """
    if not entries:
        return {"error": "no evaluated entries"}

    n = len(entries)
    thresholds = {}

    for t in range(1, 7):
        count = sum(
            1 for e in entries
            if e["accuracy"]["best"].get("positional_hits", 0) >= t
        )
        thresholds[f"pos_ge_{t}"] = {
            "count": count,
            "rate":  round(count / n * 100, 2),
        }

    # Digit hit thresholds
    digit_thresholds = {}
    for t in range(1, 7):
        count = sum(
            1 for e in entries
            if e["accuracy"]["best"].get("digit_hits", 0) >= t
        )
        digit_thresholds[f"dig_ge_{t}"] = {
            "count": count,
            "rate":  round(count / n * 100, 2),
        }

    exact = sum(1 for e in entries if e["accuracy"].get("any_exact_match"))

    return {
        "total_evaluated":       n,
        "exact_match_count":     exact,
        "exact_match_rate":      round(exact / n * 100, 2),
        "positional_thresholds": thresholds,
        "digit_thresholds":      digit_thresholds,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  2. Digit Accuracy Analysis
# ═══════════════════════════════════════════════════════════════════════════

def compute_digit_accuracy(entries: list[dict]) -> dict:
    """
    Per-position accuracy: how often each position was correctly predicted.
    Per-digit accuracy: how often each digit (0-9) was correctly placed.
    """
    if not entries:
        return {"error": "no data"}

    pos_correct = Counter()
    pos_total   = Counter()
    digit_correct = Counter()   # digit was at correct position
    digit_total   = Counter()   # digit was predicted at any position

    for e in entries:
        actual = e.get("actual_result", "")
        if len(actual) != 6:
            continue

        best_cand = e["accuracy"]["best"].get("candidate", "")
        if len(best_cand) != 6:
            continue

        for i in range(6):
            col = DIGIT_COLS[i]
            pos_total[col] += 1
            pred_d = best_cand[i]
            act_d  = actual[i]
            digit_total[pred_d] += 1

            if pred_d == act_d:
                pos_correct[col] += 1
                digit_correct[pred_d] += 1

    # Position accuracy
    position_acc = {}
    for col in DIGIT_COLS:
        tot = pos_total.get(col, 0)
        cor = pos_correct.get(col, 0)
        position_acc[col] = {
            "correct": cor,
            "total":   tot,
            "rate":    round(cor / tot * 100, 2) if tot else 0,
        }

    # Digit accuracy
    digit_acc = {}
    for d in range(10):
        ds = str(d)
        tot = digit_total.get(ds, 0)
        cor = digit_correct.get(ds, 0)
        digit_acc[ds] = {
            "correct": cor,
            "total":   tot,
            "rate":    round(cor / tot * 100, 2) if tot else 0,
        }

    return {
        "position_accuracy": position_acc,
        "digit_accuracy":    digit_acc,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  3. Model Score (Composite)
# ═══════════════════════════════════════════════════════════════════════════

def compute_model_score(entries: list[dict]) -> dict:
    """
    Composite weighted score:
      - 30% positional accuracy (avg pos hits / 6)
      - 30% digit accuracy      (avg digit hits / 6)
      - 20% consistency         (1 - σ of pos_hits / 6)
      - 10% confidence calibration (lower is better if overconfident)
      - 10% exact match bonus

    Result: 0-100 score.
    """
    if not entries:
        return {"score": 0, "grade": "N/A", "detail": {}}

    n = len(entries)

    # Collect metrics
    pos_hits_list  = [e["accuracy"]["best"].get("positional_hits", 0) for e in entries]
    dig_hits_list  = [e["accuracy"]["best"].get("digit_hits", 0)      for e in entries]
    exact_list     = [1 if e["accuracy"].get("any_exact_match") else 0 for e in entries]
    conf_list      = [e["accuracy"]["best"].get("confidence", 50)     for e in entries]

    avg_pos     = sum(pos_hits_list) / n
    avg_dig     = sum(dig_hits_list) / n
    avg_exact   = sum(exact_list) / n

    # Standard deviation of positional hits
    if n > 1:
        sigma_pos = math.sqrt(sum((x - avg_pos) ** 2 for x in pos_hits_list) / n)
    else:
        sigma_pos = 0

    consistency = max(0, 1 - sigma_pos / 6)

    # Confidence calibration: is high confidence = high accuracy?
    # Simple: abs(avg_confidence - avg_pos_hit_rate)
    avg_conf  = sum(conf_list) / n / 100   # normalise to 0-1
    avg_pos_r = avg_pos / 6
    calib_err = abs(avg_conf - avg_pos_r)
    calibration = max(0, 1 - calib_err)

    # Weighted composite
    raw = (
        0.30 * (avg_pos / 6) +
        0.30 * (avg_dig / 6) +
        0.20 * consistency +
        0.10 * calibration +
        0.10 * avg_exact
    )
    score = round(raw * 100, 1)

    # Grade
    if score >= 80: grade = "A  ⭐"
    elif score >= 60: grade = "B  ✅"
    elif score >= 40: grade = "C  ⚠️"
    elif score >= 20: grade = "D  🔻"
    else: grade = "F  ❌"

    return {
        "score": score,
        "grade": grade,
        "detail": {
            "avg_positional_hits": round(avg_pos, 2),
            "avg_digit_hits":      round(avg_dig, 2),
            "consistency":         round(consistency, 4),
            "calibration":         round(calibration, 4),
            "exact_match_rate":    round(avg_exact, 4),
            "sigma_pos_hits":      round(sigma_pos, 4),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Performance Analyzer
# ═══════════════════════════════════════════════════════════════════════════

class PerformanceAnalyzer:

    def __init__(self):
        self.entries: list[dict] = []
        self.results: dict = {}

    def load(self) -> "PerformanceAnalyzer":
        self.entries = _load_history()
        print(f"[INFO] Loaded {len(self.entries)} evaluated predictions")
        return self

    def analyze(self) -> dict:
        if not self.entries:
            self.results = {"error": "No evaluated predictions — use prediction_history.py first"}
            return self.results

        self.results["hit_rate"]        = compute_hit_rate(self.entries)
        self.results["digit_accuracy"]  = compute_digit_accuracy(self.entries)
        self.results["model_score"]     = compute_model_score(self.entries)
        self.results["meta"] = {
            "evaluated":   len(self.entries),
            "analyzed_at": datetime.now().isoformat(),
        }
        return self.results

    def to_json(self, indent=2) -> str:
        return json.dumps(self.results, ensure_ascii=False, indent=indent, default=str)

    def print_report(self):
        r = self.results
        if "error" in r:
            print(f"\n⚠  {r['error']}")
            return

        meta  = r["meta"]
        score = r["model_score"]
        hr    = r["hit_rate"]
        da    = r["digit_accuracy"]

        print("\n" + "=" * 62)
        print("  🏅 PERFORMANCE ANALYZER")
        print("=" * 62)
        print(f"  Evaluated predictions: {meta['evaluated']}")
        print(f"  Analyzed at: {meta['analyzed_at'][:19]}")

        # Model Score
        print(f"\n─── 🎯 MODEL SCORE ──────────────────────────────")
        print(f"  Score: {score['score']} / 100   Grade: {score['grade']}")
        d = score["detail"]
        print(f"  Avg pos hits  : {d['avg_positional_hits']:.2f} / 6")
        print(f"  Avg digit hits: {d['avg_digit_hits']:.2f} / 6")
        print(f"  Consistency   : {d['consistency']:.1%}")
        print(f"  Calibration   : {d['calibration']:.1%}")
        print(f"  Exact match % : {d['exact_match_rate']:.1%}")

        # Hit Rate
        print(f"\n─── 📊 HIT RATE (positional) ─────────────────────")
        print(f"  Exact matches: {hr['exact_match_count']} ({hr['exact_match_rate']}%)")
        for key, val in hr["positional_thresholds"].items():
            t = key.split("_")[-1]
            bar = "█" * int(val["rate"] / 5)
            print(f"  ≥{t} pos hit: {val['count']}/{hr['total_evaluated']}  ({val['rate']}%)  {bar}")

        print(f"\n─── 📊 HIT RATE (digit present) ─────────────────")
        for key, val in hr["digit_thresholds"].items():
            t = key.split("_")[-1]
            bar = "█" * int(val["rate"] / 5)
            print(f"  ≥{t} dig hit: {val['count']}/{hr['total_evaluated']}  ({val['rate']}%)  {bar}")

        # Position accuracy
        print(f"\n─── 🔢 POSITION ACCURACY ────────────────────────")
        for col, info in da.get("position_accuracy", {}).items():
            bar = "█" * int(info["rate"] / 5)
            print(f"  {col}: {info['correct']}/{info['total']}  ({info['rate']}%)  {bar}")

        # Digit accuracy
        print(f"\n─── 🔢 DIGIT ACCURACY ──────────────────────────")
        for d_str, info in da.get("digit_accuracy", {}).items():
            if info["total"] > 0:
                bar = "█" * int(info["rate"] / 5)
                print(f"  digit {d_str}: {info['correct']}/{info['total']}  ({info['rate']}%)  {bar}")

        print("\n" + "=" * 62)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Prediction Performance Analyzer")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--save", type=str, default="")
    args = parser.parse_args()

    analyzer = PerformanceAnalyzer()
    analyzer.load()
    analyzer.analyze()

    if args.json:
        print(analyzer.to_json())
    else:
        analyzer.print_report()

    if args.save:
        p = Path(args.save)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(analyzer.to_json(), encoding="utf-8")
        print(f"\n[INFO] Saved → {p}")


if __name__ == "__main__":
    main()
