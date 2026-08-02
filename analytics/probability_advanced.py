"""
Advanced Probability Engine
=============================
Deep conditional and transitional probability analysis for Thai lottery digits.

Input:  database/dataset/lottery_history.csv
Cols:   draw_date, digit1 … digit6

Analyses:
  1. Conditional Probability  — P(digit_j | digit_i appeared at position_k)
  2. Digit Transition Matrix  — P(digit_next_draw | digit_this_draw) per position
  3. Hot Digits               — above-expected frequency in recent N draws
  4. Cold Digits              — below-expected frequency in recent N draws

Usage:
  python analytics/probability_advanced.py
  python analytics/probability_advanced.py --window 30
  python analytics/probability_advanced.py --json
  python analytics/probability_advanced.py --save adv_prob.json
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
BASE_DIR    = Path(__file__).resolve().parents[1]
DEFAULT_CSV = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
DIGIT_COLS  = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]
ALL_DIGITS  = [str(d) for d in range(10)]


# ---------------------------------------------------------------------------
# Data loading (sorted by draw_date ascending for transition analysis)
# ---------------------------------------------------------------------------

def load(path: Path) -> list[dict]:
    if not path.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if all(row.get(c, "").isdigit() for c in DIGIT_COLS):
                rows.append(row)
    # Sort ascending (oldest first) — needed for transition analysis
    rows.sort(key=lambda r: r.get("draw_date", ""))
    print(f"[INFO] Loaded {len(rows)} valid draws")
    return rows


# ═══════════════════════════════════════════════════════════════════════════
#  1. Conditional Probability
# ═══════════════════════════════════════════════════════════════════════════

def conditional_probability(rows: list[dict]) -> dict:
    """
    P(digit at pos_j | digit at pos_i = X)
    For every position pair (i → j) and every conditioning digit X,
    returns distribution over 0-9 at the target position.
    """
    results = {}

    for i, src_col in enumerate(DIGIT_COLS):
        for j, tgt_col in enumerate(DIGIT_COLS):
            if i == j:
                continue

            key = f"{src_col}→{tgt_col}"
            cond: dict[str, Counter] = {d: Counter() for d in ALL_DIGITS}

            for row in rows:
                src_digit = row[src_col]
                tgt_digit = row[tgt_col]
                cond[src_digit][tgt_digit] += 1

            cond_probs = {}
            for src_d in ALL_DIGITS:
                total = sum(cond[src_d].values())
                if total == 0:
                    continue
                dist = {}
                for tgt_d in ALL_DIGITS:
                    cnt = cond[src_d].get(tgt_d, 0)
                    dist[tgt_d] = {
                        "count": cnt,
                        "prob": round(cnt / total, 4),
                    }
                most = max(dist, key=lambda d: dist[d]["prob"])
                least = min(dist, key=lambda d: dist[d]["prob"])
                cond_probs[src_d] = {
                    "total": total,
                    "most_likely": most,
                    "least_likely": least,
                    "distribution": dist,
                }

            results[key] = cond_probs

    return results


def conditional_summary(cond: dict) -> dict:
    """Compact summary — only adjacent position pairs, top-3 per digit."""
    summary = {}
    adj_keys = [f"digit{i}→digit{i+1}" for i in range(1, 6)]

    for key in adj_keys:
        data = cond.get(key, {})
        sm = {}
        for src_d, info in data.items():
            dist = info.get("distribution", {})
            top3 = sorted(dist.items(), key=lambda x: x[1]["prob"], reverse=True)[:3]
            sm[src_d] = {
                "most_likely": info["most_likely"],
                "top3": [{"digit": d, "prob": v["prob"]} for d, v in top3],
            }
        summary[key] = sm

    return summary


# ═══════════════════════════════════════════════════════════════════════════
#  2. Digit Transition Matrix (draw-to-draw)
# ═══════════════════════════════════════════════════════════════════════════

def transition_matrix(rows: list[dict]) -> dict:
    """
    P(digit_next | digit_current) per position.
    Tracks how each digit at a position transitions to
    the digit at the SAME position in the NEXT draw.
    """
    results = {}

    for col in DIGIT_COLS:
        trans: dict[str, Counter] = {d: Counter() for d in ALL_DIGITS}

        for idx in range(len(rows) - 1):
            cur = rows[idx][col]
            nxt = rows[idx + 1][col]
            trans[cur][nxt] += 1

        mat = {}
        for src in ALL_DIGITS:
            total = sum(trans[src].values())
            if total == 0:
                mat[src] = {d: 0.0 for d in ALL_DIGITS}
                continue
            mat[src] = {}
            for tgt in ALL_DIGITS:
                mat[src][tgt] = round(trans[src].get(tgt, 0) / total, 4)

        # Streak & repeat stats
        repeats = sum(1 for idx in range(len(rows) - 1) if rows[idx][col] == rows[idx + 1][col])
        repeat_rate = round(repeats / max(len(rows) - 1, 1), 4)

        results[col] = {
            "matrix": mat,
            "repeat_rate": repeat_rate,
            "repeat_pct": round(repeat_rate * 100, 2),
        }

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  3. Hot Digits
# ═══════════════════════════════════════════════════════════════════════════

def hot_digits(rows: list[dict], window: int = 50) -> dict:
    """
    Digits appearing significantly MORE than expected (10%) in
    the last `window` draws. Uses z-score for significance.
    """
    recent = rows[-window:]  # last N draws (ascending order)
    expected = 1 / 10
    n_obs = len(recent) * 6  # total digit observations

    # Overall hot
    overall = Counter()
    for row in recent:
        for col in DIGIT_COLS:
            overall[row[col]] += 1

    hot = []
    for d in ALL_DIGITS:
        cnt = overall.get(d, 0)
        obs_freq = cnt / n_obs if n_obs else 0
        # z = (observed - expected) / sqrt(expected * (1-expected) / n)
        se = (expected * (1 - expected) / n_obs) ** 0.5 if n_obs else 1
        z = (obs_freq - expected) / se if se > 0 else 0
        hot.append({
            "digit": d,
            "count": cnt,
            "frequency": round(obs_freq, 5),
            "pct": round(obs_freq * 100, 2),
            "z_score": round(z, 3),
            "status": "🔥 HOT" if z > 1.0 else ("OK" if z > -1.0 else "COLD"),
        })

    hot.sort(key=lambda x: x["z_score"], reverse=True)

    # Per-position hot
    per_pos = {}
    for col in DIGIT_COLS:
        pos_counter = Counter(row[col] for row in recent)
        total = sum(pos_counter.values())
        ranked = sorted(
            [{"digit": d, "count": pos_counter.get(d, 0),
              "pct": round(pos_counter.get(d, 0) / total * 100, 2)}
             for d in ALL_DIGITS],
            key=lambda x: x["count"], reverse=True
        )
        per_pos[col] = {
            "top3_hot": ranked[:3],
            "top3_cold": ranked[-3:],
        }

    return {
        "window": window,
        "total_observations": n_obs,
        "overall": hot,
        "per_position": per_pos,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  4. Cold Digits
# ═══════════════════════════════════════════════════════════════════════════

def cold_digits(rows: list[dict], window: int = 50) -> dict:
    """
    Digits that have NOT appeared or appeared rarely in last `window` draws.
    Also computes 'gap' — how many draws since each digit last appeared.
    """
    recent = rows[-window:]
    all_rows = rows  # full history for gap calc

    # --- Gap analysis (draws since last seen) ---
    last_seen: dict[str, int] = {d: -1 for d in ALL_DIGITS}
    per_pos_last: dict[str, dict[str, int]] = {col: {d: -1 for d in ALL_DIGITS} for col in DIGIT_COLS}

    for idx, row in enumerate(all_rows):
        for col in DIGIT_COLS:
            d = row[col]
            last_seen[d] = idx
            per_pos_last[col][d] = idx

    total_draws = len(all_rows)
    gaps = {}
    for d in ALL_DIGITS:
        if last_seen[d] >= 0:
            gap = total_draws - 1 - last_seen[d]
        else:
            gap = total_draws
        gaps[d] = gap

    # --- Frequency in recent window ---
    recent_counter = Counter()
    for row in recent:
        for col in DIGIT_COLS:
            recent_counter[row[col]] += 1

    n_obs = len(recent) * 6
    cold = []
    for d in ALL_DIGITS:
        cnt = recent_counter.get(d, 0)
        freq = cnt / n_obs if n_obs else 0
        cold.append({
            "digit": d,
            "recent_count": cnt,
            "recent_pct": round(freq * 100, 2),
            "gap_draws": gaps[d],
            "status": "❄️ COLD" if freq < 0.08 else ("OVERDUE" if gaps[d] > 5 else "OK"),
        })

    cold.sort(key=lambda x: x["recent_count"])

    # Per-position gaps
    pos_gaps = {}
    for col in DIGIT_COLS:
        pg = []
        for d in ALL_DIGITS:
            ls = per_pos_last[col][d]
            gap = (total_draws - 1 - ls) if ls >= 0 else total_draws
            pg.append({"digit": d, "gap": gap})
        pg.sort(key=lambda x: x["gap"], reverse=True)
        pos_gaps[col] = pg[:5]  # top 5 overdue per position

    return {
        "window": window,
        "overall": cold,
        "position_overdue": pos_gaps,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Master Engine
# ═══════════════════════════════════════════════════════════════════════════

class AdvancedProbabilityEngine:

    def __init__(self, csv_path: str | Path = DEFAULT_CSV, window: int = 50):
        self.csv_path = Path(csv_path)
        self.window = window
        self.rows: list[dict] = []
        self.results: dict = {}

    def load(self) -> "AdvancedProbabilityEngine":
        self.rows = load(self.csv_path)
        return self

    def run_all(self) -> dict:
        if not self.rows:
            return {"error": "No data loaded"}

        print("[INFO] Computing conditional probability…")
        full_cond = conditional_probability(self.rows)
        self.results["conditional_summary"] = conditional_summary(full_cond)

        print("[INFO] Computing digit transition matrix…")
        self.results["transition_matrix"] = transition_matrix(self.rows)

        print("[INFO] Detecting hot digits…")
        self.results["hot_digits"] = hot_digits(self.rows, self.window)

        print("[INFO] Detecting cold digits…")
        self.results["cold_digits"] = cold_digits(self.rows, self.window)

        self.results["meta"] = {
            "total_draws": len(self.rows),
            "window": self.window,
            "analyzed_at": datetime.now().isoformat(),
        }

        print(f"[INFO] All analyses complete ({len(self.rows)} draws)")
        return self.results

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.results, ensure_ascii=False, indent=indent, default=str)

    def print_summary(self) -> None:
        r = self.results
        if "error" in r:
            print(f"\n⚠  {r['error']}")
            return

        meta = r["meta"]
        w = meta["window"]
        print("\n" + "=" * 62)
        print("  ADVANCED PROBABILITY ENGINE — RESULTS")
        print(f"  {meta['total_draws']} draws | window={w}")
        print("=" * 62)

        # ── Conditional ──
        cs = r.get("conditional_summary", {})
        print("\n─── CONDITIONAL PROBABILITY (adjacent positions) ────")
        for key, data in cs.items():
            print(f"\n  {key}:")
            for src_d, info in list(data.items()):
                top = info["top3"]
                top_str = "  ".join(f"{t['digit']}={t['prob']:.2%}" for t in top)
                print(f"    if {key.split('→')[0][-1]}={src_d} → {top_str}")

        # ── Transition ──
        tm = r.get("transition_matrix", {})
        print("\n─── DIGIT TRANSITION (same position, next draw) ─────")
        for col, info in tm.items():
            rr = info["repeat_pct"]
            mat = info["matrix"]
            # Find strongest transition per digit
            strongest = []
            for src in ALL_DIGITS:
                best = max(ALL_DIGITS, key=lambda d: mat[src].get(d, 0))
                strongest.append(f"{src}→{best}({mat[src][best]:.0%})")
            print(f"  {col}  repeat={rr}%  │ {', '.join(strongest[:5])}")

        # ── Hot ──
        hd = r.get("hot_digits", {})
        print(f"\n─── 🔥 HOT DIGITS (last {w} draws) ──────────────────")
        for item in hd.get("overall", []):
            if item["z_score"] > 0:
                bar = "█" * int(item["pct"] * 2)
                print(f"  digit {item['digit']}: {bar:<28} {item['pct']:5.2f}%  z={item['z_score']:+.2f}  {item['status']}")

        # ── Cold ──
        cd = r.get("cold_digits", {})
        print(f"\n─── ❄️  COLD DIGITS (last {w} draws) ─────────────────")
        for item in cd.get("overall", []):
            if item["recent_pct"] < 10.5:
                print(f"  digit {item['digit']}: {item['recent_pct']:5.2f}%  gap={item['gap_draws']} draws  {item['status']}")

        # ── Position overdue ──
        po = cd.get("position_overdue", {})
        print(f"\n─── POSITION OVERDUE (most draws since last seen) ───")
        for col, items in po.items():
            overdue = [f"{it['digit']}(gap={it['gap']})" for it in items[:3]]
            print(f"  {col}: {', '.join(overdue)}")

        print("\n" + "=" * 62)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Advanced Probability Engine")
    parser.add_argument("--csv",    type=str, default=str(DEFAULT_CSV))
    parser.add_argument("--window", type=int, default=50)
    parser.add_argument("--json",   action="store_true")
    parser.add_argument("--save",   type=str, default="")
    args = parser.parse_args()

    engine = AdvancedProbabilityEngine(args.csv, args.window)
    engine.load().run_all()

    if args.json:
        print(engine.to_json())
    else:
        engine.print_summary()

    if args.save:
        p = Path(args.save)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(engine.to_json(), encoding="utf-8")
        print(f"\n[INFO] Saved → {p}")


if __name__ == "__main__":
    main()
