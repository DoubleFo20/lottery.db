"""
Ensemble Prediction Model
===========================
Combines signals from multiple analytics engines to generate
scored candidate lottery numbers.

Engines used:
  1. PatternEngine     — digit clusters, hot/cold, pair/sub-seq patterns
  2. ProbabilityEngine — positional frequency, pair & triple probabilities
  3. HeatmapEngine     — rolling heat, temporal trends, co-occurrence
  4. AdvancedProbability — conditional P, transition matrix, hot/cold z-scores

Strategy:
  For each digit position (1-6) a composite score is built per candidate
  digit (0-9) by weighting signals from all engines.  The top-K scoring
  6-digit combinations are returned as predictions.

Usage:
  python ensemble_model/predictor.py
  python ensemble_model/predictor.py --top 10
  python ensemble_model/predictor.py --json
  python ensemble_model/predictor.py --save predictions.json
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
from datetime import datetime
from itertools import combinations, product
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR    = Path(__file__).resolve().parents[1]
CSV_PATH    = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
DIGIT_COLS  = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]
ALL_DIGITS  = list(range(10))

# Ensemble weights — tuned to balance recency vs history
WEIGHTS = {
    "positional_freq":      0.20,   # historical base rate
    "rolling_heat":         0.20,   # recent hot/cold
    "conditional":          0.15,   # conditional P from previous position
    "transition":           0.10,   # draw-to-draw transition
    "pair_lift":            0.10,   # adjacent pair strength
    "pattern_hot":          0.10,   # pattern engine hot digits
    "gap_overdue":          0.08,   # cold/overdue reversion
    "temporal_trend":       0.07,   # era-specific trends
}


# ═══════════════════════════════════════════════════════════════════════════
#  Data Loading
# ═══════════════════════════════════════════════════════════════════════════

def load_rows(path: Path) -> list[dict]:
    if not path.exists():
        print(f"[ERROR] CSV not found: {path}", file=sys.stderr)
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if all(row.get(c, "").isdigit() for c in DIGIT_COLS):
                rows.append(row)
    return rows


# ═══════════════════════════════════════════════════════════════════════════
#  Signal Extractors  (self-contained — no external imports needed)
# ═══════════════════════════════════════════════════════════════════════════

def _positional_freq(rows: list[dict]) -> dict[str, dict[int, float]]:
    """P(digit | position)"""
    result = {}
    for col in DIGIT_COLS:
        cnt = Counter(int(r[col]) for r in rows)
        total = sum(cnt.values())
        result[col] = {d: cnt.get(d, 0) / total for d in ALL_DIGITS}
    return result


def _rolling_heat(rows: list[dict], window: int = 50) -> dict[str, dict[int, float]]:
    """Per-position frequency in last N draws."""
    recent = rows[:window]   # rows are desc-sorted
    result = {}
    for col in DIGIT_COLS:
        cnt = Counter(int(r[col]) for r in recent)
        total = sum(cnt.values())
        result[col] = {d: cnt.get(d, 0) / total for d in ALL_DIGITS}
    return result


def _conditional_prob(rows: list[dict]) -> dict[str, dict[int, dict[int, float]]]:
    """P(digit_j | digit_i) for adjacent positions."""
    result = {}
    for idx in range(5):
        src, tgt = DIGIT_COLS[idx], DIGIT_COLS[idx + 1]
        key = f"{src}->{tgt}"
        cond: dict[int, Counter] = {d: Counter() for d in ALL_DIGITS}
        for row in rows:
            s, t = int(row[src]), int(row[tgt])
            cond[s][t] += 1
        probs: dict[int, dict[int, float]] = {}
        for s_d in ALL_DIGITS:
            total = sum(cond[s_d].values())
            probs[s_d] = {t_d: cond[s_d].get(t_d, 0) / total if total else 0.1
                          for t_d in ALL_DIGITS}
        result[key] = probs
    return result


def _transition_matrix(rows: list[dict]) -> dict[str, dict[int, dict[int, float]]]:
    """P(digit_next_draw | digit_this_draw) per position."""
    result = {}
    for col in DIGIT_COLS:
        trans: dict[int, Counter] = {d: Counter() for d in ALL_DIGITS}
        for idx in range(len(rows) - 1):
            cur = int(rows[idx][col])
            nxt = int(rows[idx + 1][col])
            trans[cur][nxt] += 1
        mat: dict[int, dict[int, float]] = {}
        for s in ALL_DIGITS:
            total = sum(trans[s].values())
            mat[s] = {t: trans[s].get(t, 0) / total if total else 0.1
                      for t in ALL_DIGITS}
        result[col] = mat
    return result


def _pair_lift(rows: list[dict]) -> dict[str, dict[tuple, float]]:
    """Lift metric for adjacent digit pairs."""
    pos_marginals: dict[str, dict[int, float]] = {}
    for col in DIGIT_COLS:
        cnt = Counter(int(r[col]) for r in rows)
        total = sum(cnt.values())
        pos_marginals[col] = {d: cnt.get(d, 0) / total for d in ALL_DIGITS}

    result = {}
    for idx in range(5):
        col_a, col_b = DIGIT_COLS[idx], DIGIT_COLS[idx + 1]
        pair_cnt: Counter = Counter()
        total = 0
        for row in rows:
            pair_cnt[(int(row[col_a]), int(row[col_b]))] += 1
            total += 1
        lifts = {}
        for (a, b), cnt in pair_cnt.items():
            p_ab = cnt / total
            p_a = pos_marginals[col_a].get(a, 0.1)
            p_b = pos_marginals[col_b].get(b, 0.1)
            lifts[(a, b)] = p_ab / (p_a * p_b) if (p_a * p_b) > 0 else 1.0
        result[f"{col_a}->{col_b}"] = lifts
    return result


def _pattern_hot_cold(rows: list[dict]) -> dict[str, dict[int, float]]:
    """Global hot/cold bias from pattern engine logic."""
    global_cnt = Counter()
    for row in rows:
        for col in DIGIT_COLS:
            global_cnt[int(row[col])] += 1
    total = sum(global_cnt.values())
    expected = total / 10
    scores = {}
    for d in ALL_DIGITS:
        obs = global_cnt.get(d, 0)
        scores[d] = obs / expected   # > 1 = hot, < 1 = cold
    # Apply per-position
    result = {col: dict(scores) for col in DIGIT_COLS}
    return result


def _gap_overdue(rows: list[dict]) -> dict[str, dict[int, float]]:
    """Score based on how many draws since digit last appeared at position."""
    result = {}
    for col in DIGIT_COLS:
        last_seen = {}
        for idx, row in enumerate(rows):
            d = int(row[col])
            if d not in last_seen:
                last_seen[d] = idx
        scores = {}
        for d in ALL_DIGITS:
            gap = last_seen.get(d, len(rows))
            # Logarithmic scaling — bigger gap = higher overdue score
            scores[d] = math.log2(1 + gap) / math.log2(1 + len(rows))
        result[col] = scores
    return result


def _temporal_trend(rows: list[dict], band_years: int = 5) -> dict[str, dict[int, float]]:
    """Frequency from the most recent temporal band."""
    # Find the latest band
    latest_year = 0
    for row in rows:
        try:
            y = int(row.get("draw_date", "2000")[:4])
            if y > latest_year:
                latest_year = y
        except ValueError:
            pass
    band_start = (latest_year // band_years) * band_years
    recent_band = [r for r in rows
                   if r.get("draw_date", "")[:4].isdigit()
                   and band_start <= int(r["draw_date"][:4]) < band_start + band_years]
    if not recent_band:
        recent_band = rows[:50]

    result = {}
    for col in DIGIT_COLS:
        cnt = Counter(int(r[col]) for r in recent_band)
        total = sum(cnt.values())
        result[col] = {d: cnt.get(d, 0) / total for d in ALL_DIGITS}
    return result


# ═══════════════════════════════════════════════════════════════════════════
#  Ensemble Scorer
# ═══════════════════════════════════════════════════════════════════════════

class EnsemblePredictor:

    def __init__(self, csv_path: str | Path = CSV_PATH, window: int = 50):
        self.csv_path = Path(csv_path)
        self.window = window
        self.rows: list[dict] = []
        self.signals: dict = {}
        self.position_scores: dict[str, dict[int, float]] = {}
        self.candidates: list[dict] = []

    def load(self) -> "EnsemblePredictor":
        self.rows = load_rows(self.csv_path)
        if self.rows:
            print(f"[INFO] Loaded {len(self.rows)} draws")
        return self

    def extract_signals(self) -> "EnsemblePredictor":
        """Extract all signals from the dataset."""
        if not self.rows:
            return self

        print("[INFO] Extracting positional frequency…")
        self.signals["positional_freq"] = _positional_freq(self.rows)

        print("[INFO] Extracting rolling heat…")
        self.signals["rolling_heat"] = _rolling_heat(self.rows, self.window)

        print("[INFO] Extracting conditional probability…")
        self.signals["conditional"] = _conditional_prob(self.rows)

        print("[INFO] Extracting transition matrix…")
        self.signals["transition"] = _transition_matrix(self.rows)

        print("[INFO] Extracting pair lift…")
        self.signals["pair_lift"] = _pair_lift(self.rows)

        print("[INFO] Extracting pattern hot/cold…")
        self.signals["pattern_hot"] = _pattern_hot_cold(self.rows)

        print("[INFO] Extracting gap/overdue scores…")
        self.signals["gap_overdue"] = _gap_overdue(self.rows)

        print("[INFO] Extracting temporal trend…")
        self.signals["temporal_trend"] = _temporal_trend(self.rows)

        return self

    def score_positions(self) -> "EnsemblePredictor":
        """
        For each position (digit1-6) and each candidate digit (0-9),
        compute a weighted composite score from all signals.
        """
        if not self.signals:
            return self

        last_draw = self.rows[0] if self.rows else {}

        for col_idx, col in enumerate(DIGIT_COLS):
            scores = {d: 0.0 for d in ALL_DIGITS}

            for d in ALL_DIGITS:
                # 1) Positional frequency
                scores[d] += (WEIGHTS["positional_freq"]
                              * self.signals["positional_freq"][col].get(d, 0.1))

                # 2) Rolling heat
                scores[d] += (WEIGHTS["rolling_heat"]
                              * self.signals["rolling_heat"][col].get(d, 0.1))

                # 3) Conditional probability (from previous position's last digit)
                if col_idx > 0:
                    prev_col = DIGIT_COLS[col_idx - 1]
                    cond_key = f"{prev_col}->{col}"
                    if cond_key in self.signals["conditional"]:
                        prev_digit = int(last_draw.get(prev_col, "0"))
                        cp = self.signals["conditional"][cond_key].get(prev_digit, {}).get(d, 0.1)
                        scores[d] += WEIGHTS["conditional"] * cp

                # 4) Transition (from same position in last draw)
                last_digit = int(last_draw.get(col, "0"))
                tp = self.signals["transition"][col].get(last_digit, {}).get(d, 0.1)
                scores[d] += WEIGHTS["transition"] * tp

                # 5) Pair lift (boost via previous position)
                if col_idx > 0:
                    prev_col = DIGIT_COLS[col_idx - 1]
                    lift_key = f"{prev_col}->{col}"
                    if lift_key in self.signals["pair_lift"]:
                        prev_d = int(last_draw.get(prev_col, "0"))
                        lift_val = self.signals["pair_lift"][lift_key].get((prev_d, d), 1.0)
                        # Normalise lift around 1.0
                        scores[d] += WEIGHTS["pair_lift"] * (lift_val / 2.0)

                # 6) Pattern hot/cold
                scores[d] += (WEIGHTS["pattern_hot"]
                              * self.signals["pattern_hot"][col].get(d, 1.0) * 0.1)

                # 7) Gap overdue
                scores[d] += (WEIGHTS["gap_overdue"]
                              * self.signals["gap_overdue"][col].get(d, 0.0))

                # 8) Temporal trend
                scores[d] += (WEIGHTS["temporal_trend"]
                              * self.signals["temporal_trend"][col].get(d, 0.1))

            # Normalise to probabilities
            total = sum(scores.values())
            if total > 0:
                scores = {d: scores[d] / total for d in ALL_DIGITS}

            self.position_scores[col] = scores

        return self

    def generate_candidates(self, top_k: int = 5, beam_width: int = 3) -> list[dict]:
        """
        Generate top-K candidate 6-digit numbers using beam search.

        beam_width = how many top digits to keep per position.
        Candidates are scored as the product of per-position scores.
        """
        if not self.position_scores:
            return []

        # Get top `beam_width` digits per position
        top_per_pos = []
        for col in DIGIT_COLS:
            ranked = sorted(self.position_scores[col].items(),
                            key=lambda x: x[1], reverse=True)
            top_per_pos.append(ranked[:beam_width])

        # Generate all combinations from beam
        raw_candidates = []
        for combo in product(*top_per_pos):
            digits = [str(d) for d, _ in combo]
            score = 1.0
            for d, s in combo:
                score *= s
            number = "".join(digits)
            raw_candidates.append({
                "number": number,
                "score": score,
                "digits": digits,
            })

        # Sort and take top-K
        raw_candidates.sort(key=lambda x: x["score"], reverse=True)
        self.candidates = raw_candidates[:top_k]

        # Normalise scores to relative confidence %
        if self.candidates:
            max_score = self.candidates[0]["score"]
            for c in self.candidates:
                c["confidence"] = round(c["score"] / max_score * 100, 2)
                c["score"] = round(c["score"], 8)

        return self.candidates

    def run(self, top_k: int = 5, beam_width: int = 3) -> list[dict]:
        """Full pipeline: load → extract → score → generate."""
        self.load()
        self.extract_signals()
        self.score_positions()
        return self.generate_candidates(top_k=top_k, beam_width=beam_width)

    def get_results(self) -> dict:
        last_draw = self.rows[0] if self.rows else {}
        return {
            "candidates": self.candidates,
            "position_scores": {
                col: {str(d): round(s, 5) for d, s in
                      sorted(scores.items(), key=lambda x: x[1], reverse=True)}
                for col, scores in self.position_scores.items()
            },
            "last_draw": {
                "date": last_draw.get("draw_date", "?"),
                "number": "".join(last_draw.get(c, "") for c in DIGIT_COLS),
            },
            "ensemble_weights": WEIGHTS,
            "meta": {
                "total_draws": len(self.rows),
                "window": self.window,
                "predicted_at": datetime.now().isoformat(),
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.get_results(), ensure_ascii=False, indent=indent, default=str)

    def print_summary(self) -> None:
        results = self.get_results()
        meta = results["meta"]
        last = results["last_draw"]

        print("\n" + "=" * 62)
        print("  🎯 ENSEMBLE PREDICTION MODEL")
        print("=" * 62)
        print(f"  Draws analysed : {meta['total_draws']}")
        print(f"  Window         : {meta['window']}")
        print(f"  Last draw      : {last['date']}  →  {last['number']}")
        print(f"  Predicted at   : {meta['predicted_at']}")

        # ── Position scores ──
        print("\n─── POSITION DIGIT SCORES (top-3 per position) ──────")
        for col, scores in results["position_scores"].items():
            top3 = list(scores.items())[:3]
            top_str = "  ".join(f"{d}={float(s)*100:.1f}%" for d, s in top3)
            print(f"  {col}: {top_str}")

        # ── Candidates ──
        print(f"\n─── 🏆 TOP CANDIDATES ──────────────────────────────")
        print(f"  {'Rank':<6} {'Number':<10} {'Score':<14} {'Confidence':<12}")
        print(f"  {'─'*6} {'─'*10} {'─'*14} {'─'*12}")
        for i, c in enumerate(results["candidates"], 1):
            bar = "█" * int(c["confidence"] / 10)
            print(f"  #{i:<5} {c['number']:<10} {c['score']:<14.8f} {c['confidence']:>6.1f}%  {bar}")

        # ── Weights ──
        print(f"\n─── ENSEMBLE WEIGHTS ───────────────────────────────")
        for name, w in sorted(WEIGHTS.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(w * 50)
            print(f"  {name:<20} {w:.0%}  {bar}")

        print("\n" + "=" * 62)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Ensemble Lottery Predictor")
    parser.add_argument("--csv",    type=str, default=str(CSV_PATH))
    parser.add_argument("--top",    type=int, default=5, help="Top-K candidates")
    parser.add_argument("--beam",   type=int, default=3, help="Beam width per position")
    parser.add_argument("--window", type=int, default=50, help="Rolling window size")
    parser.add_argument("--json",   action="store_true")
    parser.add_argument("--save",   type=str, default="")
    args = parser.parse_args()

    predictor = EnsemblePredictor(args.csv, args.window)
    predictor.run(top_k=args.top, beam_width=args.beam)

    if args.json:
        print(predictor.to_json())
    else:
        predictor.print_summary()

    if args.save:
        p = Path(args.save)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(predictor.to_json(), encoding="utf-8")
        print(f"\n[INFO] Saved → {p}")


if __name__ == "__main__":
    main()
