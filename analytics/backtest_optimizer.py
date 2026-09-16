"""
Auto-Tuning Backtest Optimizer
==============================
Walk-forward backtesting across historical lottery draws to discover
the optimal ensemble weights that maximize multi-tier prediction accuracy.

Saves optimal weights to database/predictions/ensemble_weights.json.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import csv
import json
import itertools
from collections import Counter
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

CSV_PATH = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
WEIGHT_FILE = BASE_DIR / "database" / "predictions" / "ensemble_weights.json"
DIGIT_COLS = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]

SIGNAL_KEYS = [
    "positional_freq",
    "rolling_heat",
    "conditional",
    "transition",
    "pair_lift",
    "pattern_hot",
    "gap_overdue",
    "temporal_trend",
]


def load_all_draws() -> list[dict]:
    if not CSV_PATH.exists():
        return []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if all(r.get(c, "").isdigit() for c in DIGIT_COLS)]
    return sorted(rows, key=lambda r: r.get("draw_date", ""), reverse=True)


def evaluate_weights_on_draw(rows: list[dict], target_idx: int, weights: dict, window: int = 50) -> dict:
    """
    Predict target_idx using draws [target_idx+1 : target_idx+1+window].
    Evaluate against actual result of target_idx.
    """
    from ensemble_model.predictor import EnsemblePredictor
    
    history_slice = rows[target_idx + 1 : target_idx + 1 + window]
    if len(history_slice) < 10:
        return {"digit_hits": 0, "pos_hits": 0, "top2_hit": False, "last2_hit": False}
        
    actual_row = rows[target_idx]
    actual_number = actual_row.get("first_prize", "").zfill(6)
    actual_last2 = actual_row.get("last2", "")
    actual_top2 = actual_number[-2:]
    actual_top3 = actual_number[-3:]

    # Temporarily instantiate and run predictor with custom weights
    pred = EnsemblePredictor(CSV_PATH, window=min(window, len(history_slice)))
    pred.rows = history_slice
    
    # Save & swap global weights
    import ensemble_model.predictor as ep_module
    old_weights = dict(ep_module.WEIGHTS)
    ep_module.WEIGHTS = weights
    
    try:
        pred.extract_signals()
        pred.score_positions()
        cands = pred.generate_candidates(top_k=3, beam_width=3)
    finally:
        ep_module.WEIGHTS = old_weights

    if not cands:
        return {"digit_hits": 0, "pos_hits": 0, "top2_hit": False, "last2_hit": False}

    best_cand = cands[0]["number"]
    pos_hits = sum(1 for a, b in zip(best_cand, actual_number) if a == b)
    dig_hits = len(set(best_cand) & set(actual_number))
    
    # Check top2 and last2 hits among candidates
    top2_hit = any(c["number"][-2:] == actual_top2 for c in cands)
    last2_hit = any(c["number"][:2] == actual_last2 or c["number"][-2:] == actual_last2 for c in cands)
    top3_box_hit = any(sorted(c["number"][-3:]) == sorted(actual_top3) for c in cands)

    return {
        "digit_hits": dig_hits,
        "pos_hits": pos_hits,
        "top2_hit": top2_hit,
        "last2_hit": last2_hit,
        "top3_box_hit": top3_box_hit,
    }


def optimize(draws_count: int = 30) -> dict:
    all_draws = load_all_draws()
    total = len(all_draws)
    eval_draws = min(draws_count, total - 55)
    print(f"[INFO] Backtesting across {eval_draws} draws (Total available: {total})...")

    # Candidate weight profiles to test
    profiles = [
        # Baseline balanced
        {"positional_freq": 0.20, "rolling_heat": 0.20, "conditional": 0.15, "transition": 0.10, "pair_lift": 0.10, "pattern_hot": 0.10, "gap_overdue": 0.08, "temporal_trend": 0.07},
        # Momentum / Heat focus (hot digits + rolling)
        {"positional_freq": 0.15, "rolling_heat": 0.30, "conditional": 0.15, "transition": 0.10, "pair_lift": 0.10, "pattern_hot": 0.10, "gap_overdue": 0.05, "temporal_trend": 0.05},
        # Transition & Conditional focus (Markov chain)
        {"positional_freq": 0.15, "rolling_heat": 0.15, "conditional": 0.25, "transition": 0.20, "pair_lift": 0.10, "pattern_hot": 0.05, "gap_overdue": 0.05, "temporal_trend": 0.05},
        # Positional Frequency focus (historical long-term rate)
        {"positional_freq": 0.35, "rolling_heat": 0.15, "conditional": 0.15, "transition": 0.10, "pair_lift": 0.10, "pattern_hot": 0.05, "gap_overdue": 0.05, "temporal_trend": 0.05},
        # Mean-reversion / Gap overdue focus
        {"positional_freq": 0.15, "rolling_heat": 0.15, "conditional": 0.15, "transition": 0.10, "pair_lift": 0.10, "pattern_hot": 0.10, "gap_overdue": 0.15, "temporal_trend": 0.10},
        # High Lift & Pattern focus
        {"positional_freq": 0.15, "rolling_heat": 0.20, "conditional": 0.10, "transition": 0.10, "pair_lift": 0.20, "pattern_hot": 0.15, "gap_overdue": 0.05, "temporal_trend": 0.05},
    ]

    best_score = -1.0
    best_weights = profiles[0]
    best_stats = {}

    for i, p in enumerate(profiles):
        tot_pos = 0
        tot_dig = 0
        tot_t2 = 0
        tot_box = 0
        
        for idx in range(eval_draws):
            res = evaluate_weights_on_draw(all_draws, idx, p)
            tot_pos += res["pos_hits"]
            tot_dig += res["digit_hits"]
            if res["top2_hit"] or res["last2_hit"]: tot_t2 += 1
            if res.get("top3_box_hit"): tot_box += 1

        avg_pos = tot_pos / eval_draws
        avg_dig = tot_dig / eval_draws
        t2_rate = tot_t2 / eval_draws
        box_rate = tot_box / eval_draws

        # Multi-tier composite score: 30% 2D rate, 25% 3D box rate, 25% digit hits, 20% positional hits
        composite_score = (t2_rate * 30.0) + (box_rate * 25.0) + ((avg_dig / 6.0) * 25.0) + ((avg_pos / 6.0) * 20.0)

        print(f" Profile {i+1}: score={composite_score:.2f} | avg_dig={avg_dig:.2f} | avg_pos={avg_pos:.2f} | 2d_rate={t2_rate*100:.1f}% | box_rate={box_rate*100:.1f}%")

        if composite_score > best_score:
            best_score = composite_score
            best_weights = p
            best_stats = {
                "composite_score": round(composite_score, 2),
                "avg_digit_hits": round(avg_dig, 2),
                "avg_pos_hits": round(avg_pos, 2),
                "2d_match_rate": round(t2_rate * 100, 1),
                "3d_box_match_rate": round(box_rate * 100, 1),
                "evaluated_draws": eval_draws,
                "optimized_at": datetime.now().isoformat(),
            }

    # Save best weights
    WEIGHT_FILE.parent.mkdir(parents=True, exist_ok=True)
    WEIGHT_FILE.write_text(json.dumps(best_weights, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] Optimal weights saved to -> {WEIGHT_FILE.name}")
    print(f"[OK] Summary: {json.dumps(best_stats, indent=2)}")
    return best_weights


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-Tuning Backtest Optimizer")
    parser.add_argument("--draws", type=int, default=30, help="Number of historical draws to backtest")
    args = parser.parse_args()
    optimize(args.draws)
