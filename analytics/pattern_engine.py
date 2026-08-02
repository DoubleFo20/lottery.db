"""
Deep Pattern Discovery Engine for Thai Lottery Dataset
=======================================================
Analyzes historical lottery results to discover digit clusters,
repeating number patterns, entropy metrics, and hidden correlations.

Input:  database/dataset/lottery_history.csv
Cols:   draw_date, digit1..digit6 (+ first_prize, front3_*, back3_*, last2)

Usage:
    python analytics/pattern_engine.py                      # full analysis
    python analytics/pattern_engine.py --json               # JSON output
    python analytics/pattern_engine.py --top 5              # top-N results
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import csv
import json
import math
import os
import sys
import argparse
import logging
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV = BASE_DIR / "database" / "dataset" / "lottery_history.csv"

DIGIT_COLS = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  Data Loading
# ═══════════════════════════════════════════════════════════════════════════

def load_dataset(path: Path | str = DEFAULT_CSV) -> list[dict]:
    """Load lottery CSV into list of dicts.  Returns [] if file is empty."""
    path = Path(path)
    if not path.exists():
        log.error("Dataset not found: %s", path)
        return []

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            log.warning("CSV has no header row — empty dataset")
            return []
        for row in reader:
            # Ensure digit columns exist and are single chars
            for col in DIGIT_COLS:
                row.setdefault(col, "")
            rows.append(row)

    log.info("Loaded %d draws from %s", len(rows), path)
    return rows


# ═══════════════════════════════════════════════════════════════════════════
#  1. Digit Cluster Detection
# ═══════════════════════════════════════════════════════════════════════════

def detect_digit_clusters(rows: list[dict]) -> dict[str, Any]:
    """
    Analyzes frequency distribution of each digit (0-9) across all
    positions, and detects "hot" / "cold" clusters.

    Returns:
        {
          "position_freq":  { "digit1": {"0":n, ..}, .. },
          "global_freq":    { "0": n, "1": n, ... },
          "hot_digits":     [ (digit, count), ... ],   # top-3 overall
          "cold_digits":    [ (digit, count), ... ],   # bottom-3 overall
          "position_bias":  { "digit1": { "hot": [...], "cold": [...] }, .. },
          "pair_clusters":  [ { "pair": (d,d), "count": n, "pct": f }, ... ]
        }
    """
    if not rows:
        return {"error": "No data"}

    # --- Per-position frequency ---
    pos_freq: dict[str, Counter] = {col: Counter() for col in DIGIT_COLS}
    global_freq: Counter = Counter()

    for row in rows:
        for col in DIGIT_COLS:
            d = row.get(col, "")
            if d.isdigit():
                pos_freq[col][d] += 1
                global_freq[d] += 1

    # --- Hot / cold ---
    sorted_global = global_freq.most_common()
    hot  = sorted_global[:3]
    cold = sorted_global[-3:] if len(sorted_global) >= 3 else sorted_global

    # --- Position bias (top-2 hot, bottom-2 cold per position) ---
    pos_bias = {}
    for col in DIGIT_COLS:
        mc = pos_freq[col].most_common()
        pos_bias[col] = {
            "hot":  mc[:2],
            "cold": mc[-2:] if len(mc) >= 2 else mc,
        }

    # --- Adjacent pair clusters (digit_i, digit_i+1) ---
    pair_counter: Counter = Counter()
    total_pairs = 0
    for row in rows:
        digits = [row.get(col, "") for col in DIGIT_COLS]
        for i in range(len(digits) - 1):
            if digits[i].isdigit() and digits[i + 1].isdigit():
                pair_counter[(digits[i], digits[i + 1])] += 1
                total_pairs += 1

    top_pairs = []
    for pair, cnt in pair_counter.most_common(10):
        top_pairs.append({
            "pair": pair,
            "count": cnt,
            "pct": round(cnt / total_pairs * 100, 2) if total_pairs else 0,
        })

    return {
        "position_freq": {k: dict(v) for k, v in pos_freq.items()},
        "global_freq":   dict(global_freq),
        "hot_digits":    hot,
        "cold_digits":   cold,
        "position_bias": pos_bias,
        "pair_clusters": top_pairs,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  2. Repeating Number Patterns
# ═══════════════════════════════════════════════════════════════════════════

def detect_repeating_patterns(rows: list[dict]) -> dict[str, Any]:
    """
    Finds repeating patterns in the draw history:
      - Consecutive same-digit at same position
      - Full 6-digit repeats
      - Recurring 2-digit and 3-digit sub-sequences
      - Gap analysis (distance between appearances of same number)

    Returns dict with pattern details.
    """
    if not rows:
        return {"error": "No data"}

    n = len(rows)

    # --- Position streak (same digit appearing consecutively) ---
    streaks: list[dict] = []
    for col in DIGIT_COLS:
        max_streak = 1
        streak_digit = ""
        streak_start = 0
        cur = 1
        for i in range(1, n):
            if rows[i].get(col) == rows[i - 1].get(col) and rows[i].get(col, "").isdigit():
                cur += 1
                if cur > max_streak:
                    max_streak = cur
                    streak_digit = rows[i][col]
                    streak_start = i - cur + 1
            else:
                cur = 1
        if max_streak >= 2:
            streaks.append({
                "position": col,
                "digit": streak_digit,
                "length": max_streak,
                "start_date": rows[streak_start].get("draw_date", "?"),
            })

    # --- Full 6-digit repeat check ---
    full_counter: Counter = Counter()
    for row in rows:
        num = "".join(row.get(c, "") for c in DIGIT_COLS)
        if len(num) == 6:
            full_counter[num] += 1
    repeats_6 = {k: v for k, v in full_counter.items() if v > 1}

    # --- Sub-sequence frequency (2-digit & 3-digit windows) ---
    sub2: Counter = Counter()
    sub3: Counter = Counter()
    for row in rows:
        digits = [row.get(c, "") for c in DIGIT_COLS]
        num = "".join(digits)
        for i in range(len(num) - 1):
            sub2[num[i:i+2]] += 1
        for i in range(len(num) - 2):
            sub3[num[i:i+3]] += 1

    # --- Gap analysis for each position ---
    gap_analysis: dict[str, dict] = {}
    for col in DIGIT_COLS:
        last_seen: dict[str, int] = {}
        gaps: dict[str, list[int]] = defaultdict(list)
        for i, row in enumerate(rows):
            d = row.get(col, "")
            if d.isdigit():
                if d in last_seen:
                    gaps[d].append(i - last_seen[d])
                last_seen[d] = i
        avg_gaps = {}
        for digit, g in gaps.items():
            avg_gaps[digit] = round(sum(g) / len(g), 2) if g else 0
        gap_analysis[col] = avg_gaps

    return {
        "position_streaks":     sorted(streaks, key=lambda s: s["length"], reverse=True),
        "full_number_repeats":  repeats_6,
        "top_2digit_patterns":  sub2.most_common(10),
        "top_3digit_patterns":  sub3.most_common(10),
        "gap_analysis":         gap_analysis,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  3. Digit Entropy Calculation
# ═══════════════════════════════════════════════════════════════════════════

def calculate_digit_entropy(rows: list[dict]) -> dict[str, Any]:
    """
    Calculates Shannon entropy for each digit position and overall.

    High entropy → digits are uniformly distributed (unpredictable).
    Low entropy  → some digits appear far more often (pattern present).

    Also computes:
      - Chi-squared statistic vs uniform distribution
      - Positional entropy trend over a rolling window

    Returns dict with entropy metrics.
    """
    if not rows:
        return {"error": "No data"}

    n = len(rows)
    max_entropy = math.log2(10)  # ≈ 3.3219 for uniform over 0-9

    def shannon(counter: Counter) -> float:
        total = sum(counter.values())
        if total == 0:
            return 0.0
        ent = 0.0
        for count in counter.values():
            if count > 0:
                p = count / total
                ent -= p * math.log2(p)
        return round(ent, 4)

    def chi_squared_uniform(counter: Counter) -> float:
        total = sum(counter.values())
        if total == 0:
            return 0.0
        expected = total / 10.0
        return round(sum((counter.get(str(d), 0) - expected) ** 2 / expected for d in range(10)), 4)

    # --- Per-position entropy ---
    pos_entropy: dict[str, dict] = {}
    for col in DIGIT_COLS:
        cnt = Counter(row.get(col, "") for row in rows if row.get(col, "").isdigit())
        ent = shannon(cnt)
        chi2 = chi_squared_uniform(cnt)
        pos_entropy[col] = {
            "entropy":      ent,
            "max_entropy":  round(max_entropy, 4),
            "ratio":        round(ent / max_entropy, 4) if max_entropy else 0,
            "chi_squared":  chi2,
            "interpretation": (
                "highly random" if ent > 3.2 else
                "mostly random" if ent > 3.0 else
                "some bias"     if ent > 2.5 else
                "notable bias"
            ),
        }

    # --- Global entropy ---
    global_cnt = Counter()
    for row in rows:
        for col in DIGIT_COLS:
            d = row.get(col, "")
            if d.isdigit():
                global_cnt[d] += 1
    global_ent = shannon(global_cnt)
    global_chi = chi_squared_uniform(global_cnt)

    # --- Rolling window entropy (window = 10 draws) ---
    window_size = min(10, n)
    rolling: list[dict] = []
    for start in range(0, n - window_size + 1, window_size):
        window = rows[start:start + window_size]
        cnt = Counter()
        for row in window:
            for col in DIGIT_COLS:
                d = row.get(col, "")
                if d.isdigit():
                    cnt[d] += 1
        ent = shannon(cnt)
        rolling.append({
            "window_start": window[0].get("draw_date", "?"),
            "window_end":   window[-1].get("draw_date", "?"),
            "entropy":      ent,
        })

    return {
        "position_entropy": pos_entropy,
        "global_entropy": {
            "entropy":      global_ent,
            "max_entropy":  round(max_entropy, 4),
            "ratio":        round(global_ent / max_entropy, 4) if max_entropy else 0,
            "chi_squared":  global_chi,
        },
        "rolling_entropy": rolling,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  4. Hidden Pattern Detection
# ═══════════════════════════════════════════════════════════════════════════

def detect_hidden_patterns(rows: list[dict]) -> dict[str, Any]:
    """
    Detects less-obvious patterns:
      - Odd/even distribution per position and per draw
      - High/low (0-4 vs 5-9) balance
      - Sum trends of the 6 digits
      - Digit-pair correlation (do certain digits at pos X predict pos Y?)
      - Modular arithmetic patterns (digit mod 3, mod 5)
      - Consecutive draw delta (change in digit value between draws)
      - Positional mirror check (digit1==digit6, digit2==digit5, etc.)

    Returns dict with all hidden pattern metrics.
    """
    if not rows:
        return {"error": "No data"}

    n = len(rows)

    # ---------- Odd / Even analysis ----------
    odd_even_pos: dict[str, dict] = {}
    for col in DIGIT_COLS:
        odd = sum(1 for r in rows if r.get(col, "").isdigit() and int(r[col]) % 2 == 1)
        even = sum(1 for r in rows if r.get(col, "").isdigit() and int(r[col]) % 2 == 0)
        total = odd + even
        odd_even_pos[col] = {
            "odd": odd, "even": even,
            "odd_pct": round(odd / total * 100, 1) if total else 0,
            "even_pct": round(even / total * 100, 1) if total else 0,
        }

    # Per-draw odd count distribution
    draw_odd_counts: Counter = Counter()
    for row in rows:
        odds = sum(1 for c in DIGIT_COLS if row.get(c, "").isdigit() and int(row[c]) % 2 == 1)
        draw_odd_counts[odds] += 1

    # ---------- High / Low (0-4 vs 5-9) ----------
    high_low_pos: dict[str, dict] = {}
    for col in DIGIT_COLS:
        low  = sum(1 for r in rows if r.get(col, "").isdigit() and int(r[col]) <= 4)
        high = sum(1 for r in rows if r.get(col, "").isdigit() and int(r[col]) >= 5)
        total = low + high
        high_low_pos[col] = {
            "low_0_4": low, "high_5_9": high,
            "low_pct":  round(low / total * 100, 1)  if total else 0,
            "high_pct": round(high / total * 100, 1) if total else 0,
        }

    # ---------- Digit sum trend ----------
    sum_trend: list[dict] = []
    sums_list: list[int] = []
    for row in rows:
        digits = [int(row[c]) for c in DIGIT_COLS if row.get(c, "").isdigit()]
        s = sum(digits)
        sums_list.append(s)
        sum_trend.append({
            "draw_date": row.get("draw_date", "?"),
            "digit_sum": s,
        })
    avg_sum = round(sum(sums_list) / len(sums_list), 2) if sums_list else 0
    sum_stats = {
        "avg": avg_sum,
        "min": min(sums_list) if sums_list else 0,
        "max": max(sums_list) if sums_list else 0,
        "std": round((sum((s - avg_sum) ** 2 for s in sums_list) / len(sums_list)) ** 0.5, 2) if sums_list else 0,
    }

    # ---------- Cross-position correlation ----------
    # Pearson correlation coefficient between each pair of digit positions
    correlations: list[dict] = []
    for col_a, col_b in combinations(DIGIT_COLS, 2):
        pairs = [
            (int(r[col_a]), int(r[col_b]))
            for r in rows
            if r.get(col_a, "").isdigit() and r.get(col_b, "").isdigit()
        ]
        if len(pairs) < 3:
            continue
        xs, ys = zip(*pairs)
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        cov = sum((x - mx) * (y - my) for x, y in pairs) / len(pairs)
        sx = (sum((x - mx) ** 2 for x in xs) / len(xs)) ** 0.5
        sy = (sum((y - my) ** 2 for y in ys) / len(ys)) ** 0.5
        r_val = round(cov / (sx * sy), 4) if sx and sy else 0
        if abs(r_val) > 0.1:  # only report non-trivial
            correlations.append({
                "positions": (col_a, col_b),
                "pearson_r": r_val,
                "strength": (
                    "strong" if abs(r_val) > 0.5 else
                    "moderate" if abs(r_val) > 0.3 else
                    "weak"
                ),
            })
    correlations.sort(key=lambda c: abs(c["pearson_r"]), reverse=True)

    # ---------- Modular patterns (mod 3) ----------
    mod3_pos: dict[str, dict] = {}
    for col in DIGIT_COLS:
        cnt = Counter(int(r[col]) % 3 for r in rows if r.get(col, "").isdigit())
        total = sum(cnt.values())
        mod3_pos[col] = {
            f"mod3_{k}": round(v / total * 100, 1) if total else 0
            for k, v in sorted(cnt.items())
        }

    # ---------- Consecutive draw delta ----------
    delta_stats: dict[str, dict] = {}
    for col in DIGIT_COLS:
        deltas = []
        for i in range(1, n):
            d_prev = rows[i - 1].get(col, "")
            d_curr = rows[i].get(col, "")
            if d_prev.isdigit() and d_curr.isdigit():
                deltas.append(int(d_curr) - int(d_prev))
        if deltas:
            avg_d = round(sum(deltas) / len(deltas), 3)
            delta_stats[col] = {
                "avg_delta": avg_d,
                "most_common_delta": Counter(deltas).most_common(3),
            }

    # ---------- Mirror symmetry (pos1↔pos6, pos2↔pos5, pos3↔pos4) ----------
    mirror_pairs = [("digit1", "digit6"), ("digit2", "digit5"), ("digit3", "digit4")]
    mirror_matches: dict[str, dict] = {}
    for a, b in mirror_pairs:
        matches = sum(
            1 for r in rows
            if r.get(a, "").isdigit() and r.get(b, "").isdigit() and r[a] == r[b]
        )
        total = sum(1 for r in rows if r.get(a, "").isdigit() and r.get(b, "").isdigit())
        mirror_matches[f"{a}↔{b}"] = {
            "matches": matches,
            "total": total,
            "pct": round(matches / total * 100, 2) if total else 0,
            "expected_pct": 10.0,  # 1/10 chance if uniform
        }

    return {
        "odd_even_per_position":  odd_even_pos,
        "draw_odd_count_dist":    dict(draw_odd_counts),
        "high_low_per_position":  high_low_pos,
        "digit_sum_stats":        sum_stats,
        "digit_sum_trend":        sum_trend[:20],  # first 20 for display
        "cross_correlations":     correlations[:10],
        "mod3_distribution":      mod3_pos,
        "consecutive_deltas":     delta_stats,
        "mirror_symmetry":        mirror_matches,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Master Analysis Runner
# ═══════════════════════════════════════════════════════════════════════════

class PatternEngine:
    """Orchestrates all pattern discovery analyses on the lottery dataset."""

    def __init__(self, csv_path: str | Path = DEFAULT_CSV):
        self.csv_path = Path(csv_path)
        self.rows: list[dict] = []
        self.results: dict[str, Any] = {}

    def load(self) -> "PatternEngine":
        self.rows = load_dataset(self.csv_path)
        return self

    def run_all(self) -> dict[str, Any]:
        """Run every analysis module and return combined results."""
        if not self.rows:
            return {"error": "No data loaded. Run the scraper first to populate the CSV."}

        log.info("Running digit cluster detection …")
        self.results["digit_clusters"] = detect_digit_clusters(self.rows)

        log.info("Running repeating pattern detection …")
        self.results["repeating_patterns"] = detect_repeating_patterns(self.rows)

        log.info("Calculating digit entropy …")
        self.results["entropy"] = calculate_digit_entropy(self.rows)

        log.info("Detecting hidden patterns …")
        self.results["hidden_patterns"] = detect_hidden_patterns(self.rows)

        self.results["meta"] = {
            "total_draws": len(self.rows),
            "date_range": {
                "earliest": self.rows[-1].get("draw_date", "?") if self.rows else "?",
                "latest":   self.rows[0].get("draw_date", "?")  if self.rows else "?",
            },
            "analyzed_at": datetime.now().isoformat(),
        }

        log.info("All analyses complete (%d draws)", len(self.rows))
        return self.results

    def to_json(self, indent: int = 2) -> str:
        """Serialise results to JSON (tuples → lists for JSON compat)."""
        return json.dumps(self.results, indent=indent, ensure_ascii=False, default=str)

    def print_summary(self, top_n: int = 5) -> None:
        """Print a human-readable summary to stdout."""
        r = self.results
        if "error" in r:
            print(f"\n⚠  {r['error']}")
            return

        meta = r.get("meta", {})
        print("\n" + "=" * 60)
        print("  LOTTERY DEEP PATTERN ANALYSIS")
        print("=" * 60)
        print(f"  Draws analysed : {meta.get('total_draws', 0)}")
        dr = meta.get("date_range", {})
        print(f"  Date range     : {dr.get('earliest', '?')} → {dr.get('latest', '?')}")
        print(f"  Timestamp      : {meta.get('analyzed_at', '?')}")

        # ── Clusters ──
        cl = r.get("digit_clusters", {})
        print("\n─── DIGIT CLUSTERS ─────────────────────────")
        if "hot_digits" in cl:
            print(f"  Hot digits  : {cl['hot_digits'][:top_n]}")
            print(f"  Cold digits : {cl['cold_digits'][:top_n]}")
        if "pair_clusters" in cl:
            print(f"  Top pairs   :")
            for p in cl["pair_clusters"][:top_n]:
                print(f"    {p['pair']}  → {p['count']}x  ({p['pct']}%)")

        # ── Repeating ──
        rp = r.get("repeating_patterns", {})
        print("\n─── REPEATING PATTERNS ─────────────────────")
        for s in rp.get("position_streaks", [])[:top_n]:
            print(f"  {s['position']}: digit '{s['digit']}' repeated {s['length']}x  (from {s['start_date']})")
        if rp.get("full_number_repeats"):
            print(f"  Full 6-digit repeats: {rp['full_number_repeats']}")
        else:
            print("  No full 6-digit repeats found")
        print(f"  Top 2-digit seqs: {rp.get('top_2digit_patterns', [])[:top_n]}")
        print(f"  Top 3-digit seqs: {rp.get('top_3digit_patterns', [])[:top_n]}")

        # ── Entropy ──
        ent = r.get("entropy", {})
        print("\n─── DIGIT ENTROPY ──────────────────────────")
        ge = ent.get("global_entropy", {})
        print(f"  Global entropy : {ge.get('entropy', 0)} / {ge.get('max_entropy', 0)}  "
              f"(ratio: {ge.get('ratio', 0)})")
        for col, info in ent.get("position_entropy", {}).items():
            print(f"  {col}: H={info['entropy']}  χ²={info['chi_squared']}  → {info['interpretation']}")

        # ── Hidden ──
        hp = r.get("hidden_patterns", {})
        print("\n─── HIDDEN PATTERNS ────────────────────────")
        ss = hp.get("digit_sum_stats", {})
        print(f"  Digit sum: avg={ss.get('avg',0)}  min={ss.get('min',0)}  "
              f"max={ss.get('max',0)}  σ={ss.get('std',0)}")
        corr = hp.get("cross_correlations", [])
        if corr:
            print("  Cross-position correlations:")
            for c in corr[:top_n]:
                print(f"    {c['positions']}  r={c['pearson_r']}  ({c['strength']})")
        mirror = hp.get("mirror_symmetry", {})
        if mirror:
            print("  Mirror symmetry:")
            for k, v in mirror.items():
                print(f"    {k}: {v['pct']}%  (expected ~{v['expected_pct']}%)")

        print("\n" + "=" * 60)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Lottery Deep Pattern Discovery Engine")
    parser.add_argument("--csv",  type=str, default=str(DEFAULT_CSV), help="Path to lottery CSV")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of summary")
    parser.add_argument("--top",  type=int, default=5, help="Top-N results to show")
    parser.add_argument("--save", type=str, default="", help="Save JSON results to file")
    args = parser.parse_args()

    engine = PatternEngine(args.csv)
    engine.load()
    engine.run_all()

    if args.json:
        output = engine.to_json()
        print(output)
    else:
        engine.print_summary(top_n=args.top)

    if args.save:
        save_path = Path(args.save)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(engine.to_json(), encoding="utf-8")
        log.info("Results saved to %s", save_path)


if __name__ == "__main__":
    main()
