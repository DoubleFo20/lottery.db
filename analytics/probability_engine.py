"""
Lottery Probability Engine
===========================
Statistical probability analysis for Thai lottery digit positions.

Input:  database/dataset/lottery_history.csv
Cols:   digit1..digit6

Analyses:
  1. Frequency per digit position (conditional P(digit|position))
  2. Overall digit distribution (marginal P(digit))
  3. Pair probability (P(digit_i, digit_j) for adjacent & all pairs)
  4. Triple probability (P(digit_i, digit_j, digit_k))

Usage:
  python analytics/probability_engine.py              # human summary
  python analytics/probability_engine.py --json       # JSON output
  python analytics/probability_engine.py --top 10     # top-N results
  python analytics/probability_engine.py --save prob_results.json
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import csv
import json
import logging
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR    = Path(__file__).resolve().parents[1]
DEFAULT_CSV = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
DIGIT_COLS  = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]
ALL_DIGITS  = [str(d) for d in range(10)]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  Data Loading
# ═══════════════════════════════════════════════════════════════════════════

def load_dataset(path: Path) -> list[dict]:
    if not path.exists():
        log.error("Dataset not found: %s", path)
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return []
        for row in reader:
            for col in DIGIT_COLS:
                row.setdefault(col, "")
            rows.append(row)
    log.info("Loaded %d draws from %s", len(rows), path)
    return rows


# ═══════════════════════════════════════════════════════════════════════════
#  1. Frequency Per Digit Position
# ═══════════════════════════════════════════════════════════════════════════

def positional_frequency(rows: list[dict]) -> dict[str, Any]:
    """
    P(digit | position) — conditional probability of each digit 0-9
    appearing at each of the 6 positions.

    Returns:
        {
          "digit1": {"0": { "count": n, "probability": p }, ...},
          ...
          "digit6": { ... }
        }
    """
    result = {}
    n = len(rows)

    for col in DIGIT_COLS:
        counter = Counter()
        valid = 0
        for row in rows:
            d = row.get(col, "")
            if d.isdigit():
                counter[d] += 1
                valid += 1

        pos_data = {}
        for digit in ALL_DIGITS:
            cnt = counter.get(digit, 0)
            prob = cnt / valid if valid else 0
            pos_data[digit] = {
                "count": cnt,
                "probability": round(prob, 5),
                "pct": round(prob * 100, 2),
            }

        # Sort by probability descending
        pos_data = dict(sorted(pos_data.items(), key=lambda x: x[1]["probability"], reverse=True))
        result[col] = {
            "total_draws": valid,
            "distribution": pos_data,
            "most_likely": max(pos_data, key=lambda d: pos_data[d]["probability"]),
            "least_likely": min(pos_data, key=lambda d: pos_data[d]["probability"]),
        }

    return result


# ═══════════════════════════════════════════════════════════════════════════
#  2. Overall Digit Distribution
# ═══════════════════════════════════════════════════════════════════════════

def overall_distribution(rows: list[dict]) -> dict[str, Any]:
    """
    P(digit) — marginal probability across all positions.

    Also computes:
      - Expected vs observed ratio
      - Chi-squared test statistic for uniformity
    """
    counter = Counter()
    total = 0

    for row in rows:
        for col in DIGIT_COLS:
            d = row.get(col, "")
            if d.isdigit():
                counter[d] += 1
                total += 1

    expected = total / 10.0 if total else 1
    chi2 = 0.0

    dist = {}
    for digit in ALL_DIGITS:
        cnt = counter.get(digit, 0)
        prob = cnt / total if total else 0
        obs_exp_ratio = cnt / expected if expected else 0
        chi2 += ((cnt - expected) ** 2) / expected if expected else 0

        dist[digit] = {
            "count": cnt,
            "probability": round(prob, 5),
            "pct": round(prob * 100, 2),
            "expected": round(expected, 1),
            "obs_exp_ratio": round(obs_exp_ratio, 4),
        }

    dist = dict(sorted(dist.items(), key=lambda x: x[1]["probability"], reverse=True))

    # Critical value for χ² with df=9 at p=0.05 is 16.919
    is_uniform = chi2 < 16.919

    return {
        "total_observations": total,
        "total_draws": len(rows),
        "distribution": dist,
        "chi_squared": round(chi2, 4),
        "degrees_of_freedom": 9,
        "is_uniform_p05": is_uniform,
        "interpretation": "uniform (random)" if is_uniform else "non-uniform (possible bias)",
    }


# ═══════════════════════════════════════════════════════════════════════════
#  3. Pair Probability
# ═══════════════════════════════════════════════════════════════════════════

def pair_probability(rows: list[dict]) -> dict[str, Any]:
    """
    P(digit_i, digit_j) — joint probability for digit pairs.

    Computes:
      - Adjacent pair probability (pos 1-2, 2-3, 3-4, 4-5, 5-6)
      - All position pair combinations (C(6,2) = 15 pairs)
      - Top pairs by frequency
      - Lift metric: P(A,B) / (P(A) * P(B)) — values > 1 suggest positive association
    """
    # Global marginal probabilities per position
    pos_marginals: dict[str, dict[str, float]] = {}
    for col in DIGIT_COLS:
        cnt = Counter(r.get(col, "") for r in rows if r.get(col, "").isdigit())
        total = sum(cnt.values())
        pos_marginals[col] = {d: cnt.get(d, 0) / total for d in ALL_DIGITS} if total else {}

    # --- Adjacent pairs ---
    adj_pairs: list[dict] = []
    for idx in range(5):
        col_a, col_b = DIGIT_COLS[idx], DIGIT_COLS[idx + 1]
        pair_counter: Counter = Counter()
        total_pairs = 0
        for row in rows:
            a, b = row.get(col_a, ""), row.get(col_b, "")
            if a.isdigit() and b.isdigit():
                pair_counter[(a, b)] += 1
                total_pairs += 1

        top_pairs = []
        for (a, b), cnt in pair_counter.most_common(10):
            prob = cnt / total_pairs if total_pairs else 0
            marginal_a = pos_marginals.get(col_a, {}).get(a, 0.1)
            marginal_b = pos_marginals.get(col_b, {}).get(b, 0.1)
            lift = prob / (marginal_a * marginal_b) if (marginal_a * marginal_b) > 0 else 0
            top_pairs.append({
                "pair": f"{a}{b}",
                "count": cnt,
                "probability": round(prob, 5),
                "pct": round(prob * 100, 2),
                "lift": round(lift, 3),
            })

        adj_pairs.append({
            "positions": f"{col_a}-{col_b}",
            "total_observations": total_pairs,
            "top_pairs": top_pairs,
        })

    # --- All position-pair combinations ---
    all_combos: list[dict] = []
    global_pair_counter: Counter = Counter()
    global_total = 0

    for idx_a, idx_b in combinations(range(6), 2):
        col_a, col_b = DIGIT_COLS[idx_a], DIGIT_COLS[idx_b]
        for row in rows:
            a, b = row.get(col_a, ""), row.get(col_b, "")
            if a.isdigit() and b.isdigit():
                global_pair_counter[(a, b)] += 1
                global_total += 1

    top_global = []
    for (a, b), cnt in global_pair_counter.most_common(15):
        prob = cnt / global_total if global_total else 0
        top_global.append({
            "pair": f"{a}{b}",
            "count": cnt,
            "probability": round(prob, 5),
            "pct": round(prob * 100, 2),
        })

    return {
        "adjacent_pairs": adj_pairs,
        "global_top_pairs": top_global,
        "global_total_pairs": global_total,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  4. Triple Probability
# ═══════════════════════════════════════════════════════════════════════════

def triple_probability(rows: list[dict]) -> dict[str, Any]:
    """
    P(digit_i, digit_j, digit_k) — joint probability for triples.

    Computes:
      - Consecutive triples (positions 1-2-3, 2-3-4, 3-4-5, 4-5-6)
      - First-half triple (positions 1-2-3) and second-half triple (4-5-6)
      - Global top triples across all C(6,3)=20 position combinations
    """
    # --- Consecutive triples ---
    consec_triples: list[dict] = []
    for idx in range(4):
        cols = [DIGIT_COLS[idx], DIGIT_COLS[idx + 1], DIGIT_COLS[idx + 2]]
        triple_counter: Counter = Counter()
        total = 0
        for row in rows:
            vals = [row.get(c, "") for c in cols]
            if all(v.isdigit() for v in vals):
                triple_counter[tuple(vals)] += 1
                total += 1

        top = []
        for trip, cnt in triple_counter.most_common(10):
            prob = cnt / total if total else 0
            top.append({
                "triple": "".join(trip),
                "count": cnt,
                "probability": round(prob, 5),
                "pct": round(prob * 100, 2),
            })

        consec_triples.append({
            "positions": "-".join(cols),
            "total_observations": total,
            "unique_triples": len(triple_counter),
            "top_triples": top,
        })

    # --- Half triples (first 3 digits / last 3 digits) ---
    half_triples = {}
    for label, cols in [("first_half", DIGIT_COLS[:3]), ("second_half", DIGIT_COLS[3:])]:
        triple_counter = Counter()
        total = 0
        for row in rows:
            vals = [row.get(c, "") for c in cols]
            if all(v.isdigit() for v in vals):
                triple_counter[tuple(vals)] += 1
                total += 1

        top = []
        for trip, cnt in triple_counter.most_common(10):
            prob = cnt / total if total else 0
            top.append({
                "triple": "".join(trip),
                "count": cnt,
                "probability": round(prob, 5),
                "pct": round(prob * 100, 2),
            })

        half_triples[label] = {
            "positions": "-".join(cols),
            "total_observations": total,
            "unique_triples": len(triple_counter),
            "top_triples": top,
        }

    # --- Global top triples (all C(6,3) combos) ---
    global_counter: Counter = Counter()
    global_total = 0
    for combo in combinations(range(6), 3):
        cols = [DIGIT_COLS[i] for i in combo]
        for row in rows:
            vals = [row.get(c, "") for c in cols]
            if all(v.isdigit() for v in vals):
                global_counter[tuple(vals)] += 1
                global_total += 1

    global_top = []
    for trip, cnt in global_counter.most_common(15):
        prob = cnt / global_total if global_total else 0
        global_top.append({
            "triple": "".join(trip),
            "count": cnt,
            "probability": round(prob, 5),
            "pct": round(prob * 100, 2),
        })

    return {
        "consecutive_triples": consec_triples,
        "half_triples": half_triples,
        "global_top_triples": global_top,
        "global_total": global_total,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Master Engine
# ═══════════════════════════════════════════════════════════════════════════

class ProbabilityEngine:
    """Orchestrates all probability analyses."""

    def __init__(self, csv_path: str | Path = DEFAULT_CSV):
        self.csv_path = Path(csv_path)
        self.rows: list[dict] = []
        self.results: dict[str, Any] = {}

    def load(self) -> "ProbabilityEngine":
        self.rows = load_dataset(self.csv_path)
        return self

    def run_all(self) -> dict[str, Any]:
        if not self.rows:
            return {"error": "No data loaded"}

        log.info("Computing positional frequency…")
        self.results["positional_frequency"] = positional_frequency(self.rows)

        log.info("Computing overall distribution…")
        self.results["overall_distribution"] = overall_distribution(self.rows)

        log.info("Computing pair probability…")
        self.results["pair_probability"] = pair_probability(self.rows)

        log.info("Computing triple probability…")
        self.results["triple_probability"] = triple_probability(self.rows)

        self.results["meta"] = {
            "total_draws": len(self.rows),
            "analyzed_at": datetime.now().isoformat(),
            "source": str(self.csv_path),
        }

        log.info("All probability analyses complete (%d draws)", len(self.rows))
        return self.results

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.results, indent=indent, ensure_ascii=False, default=str)

    def print_summary(self, top_n: int = 5) -> None:
        r = self.results
        if "error" in r:
            print(f"\n⚠  {r['error']}")
            return

        meta = r.get("meta", {})
        print("\n" + "=" * 62)
        print("  LOTTERY PROBABILITY ENGINE — RESULTS")
        print("=" * 62)
        print(f"  Draws analysed : {meta.get('total_draws', 0)}")
        print(f"  Timestamp      : {meta.get('analyzed_at', '?')}")

        # ── Positional ──
        pf = r.get("positional_frequency", {})
        print("\n─── POSITIONAL FREQUENCY P(digit|position) ────")
        for col in DIGIT_COLS:
            info = pf.get(col, {})
            dist = info.get("distribution", {})
            most = info.get("most_likely", "?")
            least = info.get("least_likely", "?")
            top = list(dist.items())[:3]
            top_str = "  ".join(f"{d}={v['pct']}%" for d, v in top)
            print(f"  {col}: hot={most}  cold={least}  │ {top_str}")

        # ── Overall ──
        od = r.get("overall_distribution", {})
        print("\n─── OVERALL DISTRIBUTION P(digit) ──────────────")
        dist = od.get("distribution", {})
        for d, v in list(dist.items())[:top_n]:
            bar = "█" * int(v["pct"] * 2)
            print(f"  digit {d}: {v['pct']:5.2f}%  ({v['count']})  {bar}")
        chi2 = od.get("chi_squared", 0)
        interp = od.get("interpretation", "?")
        print(f"  χ² = {chi2}  → {interp}")

        # ── Pairs ──
        pp = r.get("pair_probability", {})
        print("\n─── PAIR PROBABILITY P(d_i, d_j) ──────────────")
        for ap in pp.get("adjacent_pairs", []):
            print(f"  {ap['positions']}:")
            for p in ap.get("top_pairs", [])[:3]:
                print(f"    '{p['pair']}' → {p['pct']}%  lift={p['lift']}")

        print(f"  Global top pairs:")
        for p in pp.get("global_top_pairs", [])[:top_n]:
            print(f"    '{p['pair']}' → {p['count']}x  {p['pct']}%")

        # ── Triples ──
        tp = r.get("triple_probability", {})
        print("\n─── TRIPLE PROBABILITY P(d_i, d_j, d_k) ───────")
        for ct in tp.get("consecutive_triples", []):
            print(f"  {ct['positions']}:  ({ct['unique_triples']} unique)")
            for t in ct.get("top_triples", [])[:3]:
                print(f"    '{t['triple']}' → {t['count']}x  {t['pct']}%")

        halves = tp.get("half_triples", {})
        for label, data in halves.items():
            print(f"  {label} ({data['positions']}):")
            for t in data.get("top_triples", [])[:3]:
                print(f"    '{t['triple']}' → {t['count']}x  {t['pct']}%")

        print("\n" + "=" * 62)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Lottery Probability Engine")
    parser.add_argument("--csv",  type=str, default=str(DEFAULT_CSV))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--top",  type=int, default=5)
    parser.add_argument("--save", type=str, default="")
    args = parser.parse_args()

    engine = ProbabilityEngine(args.csv)
    engine.load()
    engine.run_all()

    if args.json:
        print(engine.to_json())
    else:
        engine.print_summary(top_n=args.top)

    if args.save:
        p = Path(args.save)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(engine.to_json(), encoding="utf-8")
        log.info("Saved to %s", p)


if __name__ == "__main__":
    main()
