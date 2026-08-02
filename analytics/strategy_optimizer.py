"""analytics/strategy_optimizer.py — Ensemble Strategy Optimizer"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parents[1]

SOURCES = {
    "monte_carlo":    BASE / "database/simulation/monte_carlo_results.json",
    "pipeline_cache": BASE / "database/predictions/pipeline_cache.json",
    "trend_scanner":  BASE / "database/trends/trend_cache.json",
}

WEIGHTS = {
    "monte_carlo":    0.20,
    "pipeline_cache": 0.55,
    "trend_scanner":  0.25,
}


def load_candidates() -> dict[str, list[dict]]:
    pool = {}
    for src, path in SOURCES.items():
        if not path.exists():
            pool[src] = []
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if src == "monte_carlo":
                pool[src] = data.get("top_candidates", [])[:50]
            elif src == "pipeline_cache":
                pool[src] = data.get("candidates", [])[:20]
            else:
                pool[src] = []
        except Exception:
            pool[src] = []
    return pool


def score_candidate(number: str, source: str, raw_score: float) -> float:
    """Normalise raw score to [0, 1]."""
    return min(1.0, max(0.0, raw_score / 100.0))


def ensemble_score(scores: dict[str, float]) -> float:
    total = 0.0
    weight_sum = 0.0
    for src, s in scores.items():
        w = WEIGHTS.get(src, 0.1)
        total += w * s
        weight_sum += w
    return round(total / weight_sum, 5) if weight_sum else 0.0


def rank_candidates(pool: dict[str, list[dict]]) -> list[dict]:
    aggregated: dict[str, dict[str, float]] = defaultdict(dict)

    for src, candidates in pool.items():
        for cand in candidates:
            num = cand.get("number") or cand.get("sequence", "")
            if not num:
                continue
            raw = cand.get("confidence") or cand.get("probability", 0)
            if isinstance(raw, float) and raw <= 1.0:
                raw *= 100
            aggregated[num][src] = score_candidate(num, src, float(raw))

    ranked = []
    for number, scores in aggregated.items():
        final = ensemble_score(scores)
        ranked.append({
            "number":     number,
            "score":      final,
            "confidence": round(final * 100, 2),
            "sources":    list(scores.keys()),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


def run_optimizer(top_k: int = 5) -> list[dict]:
    pool = load_candidates()
    ranked = rank_candidates(pool)
    return ranked[:top_k]


if __name__ == "__main__":
    top5 = run_optimizer()
    print("\n── Strategy Optimizer — Top 5 Predictions ──")
    for i, c in enumerate(top5, 1):
        print(f"  #{i}  {c['number']}  confidence={c['confidence']}%  sources={c['sources']}")
