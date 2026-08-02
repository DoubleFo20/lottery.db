"""
Prediction Pipeline Runner
============================
Runs all engines in ONE Python process and saves combined results
as a JSON cache file that the PHP API reads instantly.

Usage:
  python api/run_pipeline.py                # run + save cache
  python api/run_pipeline.py --top 10       # top-10 candidates
  python api/run_pipeline.py --print        # also print results

Output:
  database/predictions/pipeline_cache.json
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
import csv

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

CSV_PATH   = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
CACHE_PATH = BASE_DIR / "database" / "predictions" / "pipeline_cache.json"
DIGIT_COLS = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]


def read_dataset_summary():
    if not CSV_PATH.exists():
        return {"total_draws": 0, "latest": None, "latest_number": None}

    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        rows = [row for row in csv.DictReader(f) if row.get("draw_date")]

    rows.sort(key=lambda row: row.get("draw_date", ""), reverse=True)
    latest = rows[0] if rows else {}
    return {
        "total_draws": len(rows),
        "latest": latest.get("draw_date"),
        "latest_number": latest.get("first_prize"),
    }


def run_pipeline(top_k=5, beam=3, window=50):
    """Run all engines and return combined JSON-ready dict."""

    result = {"status": "ok"}

    # ── 1. Ensemble Predictor ──────────────────────────────
    print("[1/4] Running ensemble predictor...")
    from ensemble_model.predictor import EnsemblePredictor
    pred = EnsemblePredictor(CSV_PATH, window)
    pred.run(top_k=top_k, beam_width=beam)
    pred_data = pred.get_results()

    result["candidates"]       = pred_data.get("candidates", [])
    result["position_scores"]  = pred_data.get("position_scores", {})
    result["ensemble_weights"] = pred_data.get("ensemble_weights", {})
    result["last_draw"]        = pred_data.get("last_draw", {})

    # ── 2. Trend Scanner ──────────────────────────────────
    print("[2/4] Running trend scanner...")
    from trend_scanner.trend_scanner import TrendScanner
    ts = TrendScanner(CSV_PATH, window=min(window, 20))
    ts.load()
    ts.scan()
    trends = ts.results

    active_streaks = [s for s in trends.get("streaks", []) if s.get("active")]
    spikes_up   = [s for s in trends.get("spikes", []) if "SPIKE" in s.get("type", "")]
    spikes_down = [s for s in trends.get("spikes", []) if "DROP" in s.get("type", "")]

    result["analytics"] = {
        "active_streaks":   active_streaks[:5],
        "frequency_spikes": spikes_up[:8],
        "frequency_drops":  spikes_down[:8],
        "surging_2digit":   trends.get("recent_patterns", {}).get("top_surging_2digit", []),
        "surging_3digit":   trends.get("recent_patterns", {}).get("top_surging_3digit", []),
        "digit_trends":     trends.get("digit_trend_summary", {}),
    }

    # ── 3. Advanced Probability ───────────────────────────
    print("[3/4] Running advanced probability...")
    from analytics.probability_advanced import AdvancedProbabilityEngine
    adv = AdvancedProbabilityEngine(CSV_PATH, window=window)
    adv.load()
    adv_results = adv.run_all()

    result["analytics"]["hot_digits"]  = adv_results.get("hot_digits", {})
    result["analytics"]["cold_digits"] = adv_results.get("cold_digits", {})

    # ── 4. Explainable AI (top-1 only) ────────────────────
    print("[4/4] Running explainable AI...")
    from analytics.explainable_ai import ExplainableAI
    xai = ExplainableAI(CSV_PATH)
    xai.rows = pred.rows  # reuse already-loaded data
    top_number = result["candidates"][0]["number"] if result["candidates"] else ""
    if len(top_number) == 6:
        explanation = xai.explain(top_number)
        explanation["ensemble_confidence"] = result["candidates"][0].get("confidence", 0)
        result["explanation"] = explanation

    # ── Meta ──────────────────────────────────────────────
    dataset_summary = read_dataset_summary()
    result["meta"] = {
        "total_draws":   len(pred.rows),
        "latest_draw":   dataset_summary.get("latest"),
        "dataset":       dataset_summary,
        "params":        {"top": top_k, "beam": beam, "window": window},
        "processing_at": datetime.now().isoformat(),
        "api_version":   "1.0",
    }

    return result


def save_cache(data: dict):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"[OK] Saved -> {CACHE_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Prediction Pipeline Runner")
    parser.add_argument("--top",    type=int, default=5)
    parser.add_argument("--beam",   type=int, default=3)
    parser.add_argument("--window", type=int, default=50)
    parser.add_argument("--print",  action="store_true")
    args = parser.parse_args()

    data = run_pipeline(args.top, args.beam, args.window)
    save_cache(data)

    if args.print:
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))

    print(f"\n[OK] Pipeline complete - {len(data.get('candidates', []))} candidates generated")


if __name__ == "__main__":
    main()
