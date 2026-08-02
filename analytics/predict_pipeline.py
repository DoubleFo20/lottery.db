"""analytics/predict_pipeline.py — Full Lottery AI Prediction Pipeline"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

CSV_PATH    = BASE / "database" / "dataset" / "lottery_history.csv"
PRED_DIR    = BASE / "database" / "predictions"
OUT_FILE    = PRED_DIR / "pipeline_output.json"


# ── Step helpers ─────────────────────────────────────────

def load_dataset() -> list[str]:
    numbers = []
    if not CSV_PATH.exists():
        print("[WARN] Dataset missing:", CSV_PATH)
        return numbers
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            digits = "".join(row.get(f"digit{i}", "") for i in range(1, 7))
            if len(digits) == 6:
                numbers.append(digits)
    print(f"[1/6] Loaded {len(numbers)} draws")
    return numbers


def run_probability_engine(numbers: list[str]) -> list[dict]:
    from collections import Counter
    candidates = []
    for pos in range(6):
        freq = Counter(n[pos] for n in numbers if len(n) > pos)
        top  = freq.most_common(3)
        candidates.append([d for d, _ in top])

    # Build top combinations from per-position tops
    def _build(pos, current):
        if pos == 6:
            yield "".join(current)
            return
        for d in candidates[pos]:
            yield from _build(pos + 1, current + [d])

    results = [{"number": n, "source": "probability"} for n in list(_build(0, []))[:20]]
    print(f"[2/6] Probability engine: {len(results)} candidates")
    return results


def run_pattern_engine(numbers: list[str]) -> list[dict]:
    """Use last 10 draws as pattern anchors."""
    recent = numbers[-10:] if len(numbers) >= 10 else numbers
    seen = {"".join(r[i] for r in recent if i < len(r))[:6] for i in range(1)}
    results = [{"number": n, "source": "pattern"} for n in recent[-5:]]
    print(f"[3/6] Pattern engine: {len(results)} candidates")
    return results


def run_trend_scanner() -> list[dict]:
    trend_cache = BASE / "database" / "trends" / "trend_cache.json"
    if trend_cache.exists():
        try:
            data = json.loads(trend_cache.read_text(encoding="utf-8"))
            cands = data.get("candidates", [])[:10]
            print(f"[4/6] Trend scanner: {len(cands)} candidates from cache")
            return cands
        except Exception:
            pass
    print("[4/6] Trend scanner: no cache, skipped")
    return []


def run_monte_carlo() -> list[dict]:
    mc_path = BASE / "database" / "simulation" / "monte_carlo_results.json"
    if mc_path.exists():
        try:
            data  = json.loads(mc_path.read_text(encoding="utf-8"))
            cands = [{"number": c["number"], "source": "monte_carlo", "confidence": c["probability"] * 100}
                     for c in data.get("top_candidates", [])[:20]]
            print(f"[5/6] Monte Carlo: {len(cands)} candidates")
            return cands
        except Exception:
            pass
    print("[5/6] Monte Carlo: no results, skipped")
    return []


def run_strategy_optimizer(pool: list[dict]) -> list[dict]:
    from collections import defaultdict
    scores: dict[str, float] = defaultdict(float)
    counts: dict[str, int]   = defaultdict(int)
    for c in pool:
        num = c.get("number", "")
        if not num:
            continue
        scores[num] += float(c.get("confidence", 50)) / 100
        counts[num] += 1

    ranked = sorted(scores, key=lambda n: scores[n], reverse=True)
    top5 = [{"number": n, "confidence": round(scores[n] / counts[n] * 100, 2), "votes": counts[n]}
            for n in ranked[:5]]
    print(f"[6/6] Strategy optimizer: top {len(top5)} results")
    return top5


# ── Main pipeline ─────────────────────────────────────────

def run():
    print("\n==== Predict Pipeline ====")
    numbers = load_dataset()

    pool: list[dict] = []
    pool += run_probability_engine(numbers)
    pool += run_pattern_engine(numbers)
    pool += run_trend_scanner()
    pool += run_monte_carlo()

    top5 = run_strategy_optimizer(pool)

    PRED_DIR.mkdir(parents=True, exist_ok=True)
    output = {"timestamp": datetime.now().isoformat(), "top_predictions": top5}
    OUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n-- Top 5 Predictions --")
    for i, c in enumerate(top5, 1):
        print(f"  #{i}  {c['number']}  conf={c['confidence']}%  votes={c['votes']}")
    print(f"\nSaved -> {OUT_FILE}\n")
    return output


if __name__ == "__main__":
    run()
