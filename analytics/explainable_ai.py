"""
Explainable AI Module
======================
Breaks down WHY the ensemble model picked each candidate number,
attributing scores to three factors:

  - Pattern Score    (pattern_engine signals — hot/cold, pairs, streaks)
  - Probability Score (probability_engine — positional freq, pairs, triples)
  - Heatmap Score    (heatmap_engine — rolling heat, co-occurrence, temporal)

For each candidate digit in each position, a narrative explanation
is generated alongside numerical factor contributions.

Usage:
  python analytics/explainable_ai.py
  python analytics/explainable_ai.py --number 219367
  python analytics/explainable_ai.py --top 3
  python analytics/explainable_ai.py --json
  python analytics/explainable_ai.py --save explanation.json
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
from pathlib import Path

# ---------------------------------------------------------------------------
BASE_DIR   = Path(__file__).resolve().parents[1]
CSV_PATH   = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
DIGIT_COLS = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]
ALL_DIGITS = list(range(10))

# Factor weights (mirror ensemble_model/predictor.py groupings)
FACTOR_WEIGHTS = {
    "pattern":     {"gap_overdue": 0.08, "pattern_hot": 0.10},          # 18%
    "probability": {"positional_freq": 0.20, "conditional": 0.15,
                    "pair_lift": 0.10, "transition": 0.10},             # 55%
    "heatmap":     {"rolling_heat": 0.20, "temporal_trend": 0.07},      # 27%
}


# ═══════════════════════════════════════════════════════════════════════════
#  Data
# ═══════════════════════════════════════════════════════════════════════════

def load_rows(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if all(row.get(c, "").isdigit() for c in DIGIT_COLS):
                rows.append(row)
    return rows


# ═══════════════════════════════════════════════════════════════════════════
#  Raw Signal Extractors  (self-contained)
# ═══════════════════════════════════════════════════════════════════════════

def _pos_freq(rows):
    res = {}
    for col in DIGIT_COLS:
        cnt = Counter(int(r[col]) for r in rows)
        tot = sum(cnt.values())
        res[col] = {d: cnt.get(d, 0) / tot for d in ALL_DIGITS}
    return res

def _rolling_heat(rows, window=50):
    recent = rows[:window]
    res = {}
    for col in DIGIT_COLS:
        cnt = Counter(int(r[col]) for r in recent)
        tot = sum(cnt.values())
        res[col] = {d: cnt.get(d, 0) / tot for d in ALL_DIGITS}
    return res

def _gap_overdue(rows):
    res = {}
    for col in DIGIT_COLS:
        last = {}
        for idx, row in enumerate(rows):
            d = int(row[col])
            if d not in last:
                last[d] = idx
        res[col] = {
            d: math.log2(1 + last.get(d, len(rows))) / math.log2(1 + len(rows))
            for d in ALL_DIGITS
        }
    return res

def _pattern_hot(rows):
    cnt = Counter()
    for row in rows:
        for col in DIGIT_COLS:
            cnt[int(row[col])] += 1
    tot = sum(cnt.values())
    exp = tot / 10
    scores = {d: cnt.get(d, 0) / exp for d in ALL_DIGITS}
    return {col: dict(scores) for col in DIGIT_COLS}

def _conditional(rows):
    res = {}
    for idx in range(5):
        src, tgt = DIGIT_COLS[idx], DIGIT_COLS[idx + 1]
        key = f"{src}->{tgt}"
        cond = {d: Counter() for d in ALL_DIGITS}
        for row in rows:
            cond[int(row[src])][int(row[tgt])] += 1
        probs = {}
        for s in ALL_DIGITS:
            tot = sum(cond[s].values())
            probs[s] = {t: cond[s].get(t, 0) / tot if tot else 0.1 for t in ALL_DIGITS}
        res[key] = probs
    return res

def _pair_lift(rows):
    marginals = {}
    for col in DIGIT_COLS:
        cnt = Counter(int(r[col]) for r in rows)
        tot = sum(cnt.values())
        marginals[col] = {d: cnt.get(d, 0) / tot for d in ALL_DIGITS}
    res = {}
    for idx in range(5):
        ca, cb = DIGIT_COLS[idx], DIGIT_COLS[idx + 1]
        pair_cnt = Counter()
        tot = 0
        for row in rows:
            pair_cnt[(int(row[ca]), int(row[cb]))] += 1
            tot += 1
        lifts = {}
        for (a, b), cnt in pair_cnt.items():
            p_ab = cnt / tot
            p_a = marginals[ca].get(a, 0.1)
            p_b = marginals[cb].get(b, 0.1)
            lifts[(a, b)] = p_ab / (p_a * p_b) if (p_a * p_b) > 0 else 1.0
        res[f"{ca}->{cb}"] = lifts
    return res

def _transition(rows):
    res = {}
    for col in DIGIT_COLS:
        trans = {d: Counter() for d in ALL_DIGITS}
        for idx in range(len(rows) - 1):
            trans[int(rows[idx][col])][int(rows[idx + 1][col])] += 1
        mat = {}
        for s in ALL_DIGITS:
            tot = sum(trans[s].values())
            mat[s] = {t: trans[s].get(t, 0) / tot if tot else 0.1 for t in ALL_DIGITS}
        res[col] = mat
    return res

def _temporal(rows, band=5):
    latest = max(int(r["draw_date"][:4]) for r in rows if r.get("draw_date", "").isdigit() or r.get("draw_date", "")[:4].isdigit())
    bs = (latest // band) * band
    band_rows = [r for r in rows if r.get("draw_date", "")[:4].isdigit()
                 and bs <= int(r["draw_date"][:4]) < bs + band] or rows[:50]
    res = {}
    for col in DIGIT_COLS:
        cnt = Counter(int(r[col]) for r in band_rows)
        tot = sum(cnt.values())
        res[col] = {d: cnt.get(d, 0) / tot for d in ALL_DIGITS}
    return res


# ═══════════════════════════════════════════════════════════════════════════
#  Factor Scorer
# ═══════════════════════════════════════════════════════════════════════════

def _compute_factor_scores(rows: list[dict], number: str) -> list[dict]:
    """
    For each of the 6 digit positions in `number`, compute:
      - pattern_score, probability_score, heatmap_score
      - narrative explanation
    Returns list of 6 position dicts.
    """
    digits = [int(c) for c in number.ljust(6, "0")[:6]]
    last_draw = rows[0]

    # Extract all signals
    pf  = _pos_freq(rows)
    rh  = _rolling_heat(rows)
    go  = _gap_overdue(rows)
    ph  = _pattern_hot(rows)
    cp  = _conditional(rows)
    pl  = _pair_lift(rows)
    tr  = _transition(rows)
    tm  = _temporal(rows)

    positions_out = []

    for idx, col in enumerate(DIGIT_COLS):
        d = digits[idx]

        # ── Raw signal values ──
        sig = {
            "positional_freq": pf[col].get(d, 0),
            "rolling_heat":    rh[col].get(d, 0),
            "gap_overdue":     go[col].get(d, 0),
            "pattern_hot":     ph[col].get(d, 1.0) * 0.1,
            "conditional":     0.1,   # default if first position
            "pair_lift":       0.0,
            "transition":      0.1,
            "temporal_trend":  tm[col].get(d, 0),
        }

        # Conditional from previous position
        if idx > 0:
            prev_col = DIGIT_COLS[idx - 1]
            prev_d = digits[idx - 1]
            key = f"{prev_col}->{col}"
            if key in cp:
                sig["conditional"] = cp[key].get(prev_d, {}).get(d, 0.1)

        # Pair lift from previous position
        if idx > 0:
            prev_col = DIGIT_COLS[idx - 1]
            prev_d = digits[idx - 1]
            lk = f"{prev_col}->{col}"
            if lk in pl:
                lift = pl[lk].get((prev_d, d), 1.0)
                sig["pair_lift"] = lift / 2.0

        # Transition from last draw
        last_d = int(last_draw.get(col, "0"))
        sig["transition"] = tr[col].get(last_d, {}).get(d, 0.1)

        # ── Factor scores (weighted sum per factor group) ──
        pattern_score = (
            FACTOR_WEIGHTS["pattern"]["gap_overdue"]  * sig["gap_overdue"] +
            FACTOR_WEIGHTS["pattern"]["pattern_hot"]  * sig["pattern_hot"]
        )
        prob_score = (
            FACTOR_WEIGHTS["probability"]["positional_freq"] * sig["positional_freq"] +
            FACTOR_WEIGHTS["probability"]["conditional"]     * sig["conditional"] +
            FACTOR_WEIGHTS["probability"]["pair_lift"]       * sig["pair_lift"] +
            FACTOR_WEIGHTS["probability"]["transition"]      * sig["transition"]
        )
        heat_score = (
            FACTOR_WEIGHTS["heatmap"]["rolling_heat"]    * sig["rolling_heat"] +
            FACTOR_WEIGHTS["heatmap"]["temporal_trend"]  * sig["temporal_trend"]
        )

        total = pattern_score + prob_score + heat_score
        if total > 0:
            p_pct = pattern_score / total
            pr_pct = prob_score / total
            h_pct = heat_score / total
        else:
            p_pct = pr_pct = h_pct = 1/3

        # ── Narrative reasons ──
        reasons_th = []
        reasons_en = []

        # Probability reasons
        freq_pct = sig["positional_freq"] * 100
        exp_pct = 10.0
        if freq_pct > exp_pct + 1:
            reasons_th.append(f"ตัวเลข {d} ออกบ่อยกว่าค่าเฉลี่ยที่ตำแหน่งนี้ ({freq_pct:.1f}% vs {exp_pct:.0f}%)")
            reasons_en.append(f"Digit {d} appears more frequently than average here ({freq_pct:.1f}% vs {exp_pct:.0f}%)")
        elif freq_pct < exp_pct - 1:
            reasons_th.append(f"ตัวเลข {d} ออกน้อยกว่าค่าเฉลี่ยที่ตำแหน่งนี้ ({freq_pct:.1f}%)")
            reasons_en.append(f"Digit {d} appears less frequently than average here ({freq_pct:.1f}%)")

        if idx > 0 and sig["conditional"] > 0.12:
            prev = digits[idx - 1]
            reasons_th.append(f"เมื่อตำแหน่งก่อนออก {prev} มีโอกาส {sig['conditional']:.1%} ที่ตำแหน่งนี้จะออก {d}")
            reasons_en.append(f"When previous digit is {prev}, there's a {sig['conditional']:.1%} chance this digit is {d}")

        if sig["transition"] > 0.14:
            reasons_th.append(f"จากงวดก่อน ตำแหน่งนี้มักจะเปลี่ยนมาเป็น {d} ({sig['transition']:.1%})")
            reasons_en.append(f"From last draw, this position frequently transitions to {d} ({sig['transition']:.1%})")

        if idx > 0 and sig["pair_lift"] > 0.6:
            prev = digits[idx - 1]
            reasons_th.append(f"คู่ {prev}{d} มี lift สูง — ออกร่วมกันบ่อยกว่าที่ควรจะเป็น")
            reasons_en.append(f"Pair {prev}{d} has high lift — appears together more often than expected")

        # Heatmap reasons
        heat_pct = sig["rolling_heat"] * 100
        if heat_pct > 12:
            reasons_th.append(f"🔥 HOT: ออก {heat_pct:.1f}% ใน 50 งวดล่าสุด (เหนือค่าเฉลี่ย)")
            reasons_en.append(f"🔥 HOT: Appeared {heat_pct:.1f}% in last 50 draws (above average)")
        elif heat_pct < 8:
            reasons_th.append(f"❄️ COLD แต่ overdue: ออกเพียง {heat_pct:.1f}% ใน 50 งวดล่าสุด")
            reasons_en.append(f"❄️ COLD but overdue: Appeared only {heat_pct:.1f}% in last 50 draws")

        # Pattern reasons
        gap_val = go[col].get(d, 0)
        if gap_val > 0.4:
            reasons_th.append(f"ตัวเลข {d} ไม่ได้ออกมาสักพักที่ตำแหน่งนี้ (gap score={gap_val:.2f})")
            reasons_en.append(f"Digit {d} hasn't appeared recently in this position (gap score={gap_val:.2f})")

        hot_ratio = ph[col].get(d, 1.0)
        if hot_ratio > 1.1:
            reasons_th.append(f"Pattern analysis: ตัวเลข {d} เป็น hot digit ในภาพรวม ({hot_ratio:.2f}x ค่าเฉลี่ย)")
            reasons_en.append(f"Pattern analysis: Digit {d} is an overall hot digit ({hot_ratio:.2f}x average)")

        if not reasons_th:
            reasons_th.append(f"ตัวเลข {d} มีคะแนนสมดุลระหว่างทุก signal")
            reasons_en.append(f"Digit {d} has a balanced score across all signals")

        positions_out.append({
            "position": col,
            "digit": d,
            "raw_signals": {k: round(v, 5) for k, v in sig.items()},
            "factor_scores": {
                "pattern_score":     round(pattern_score, 5),
                "probability_score": round(prob_score, 5),
                "heatmap_score":     round(heat_score, 5),
                "total":             round(total, 5),
            },
            "factor_contribution": {
                "pattern_pct":     round(p_pct * 100, 1),
                "probability_pct": round(pr_pct * 100, 1),
                "heatmap_pct":     round(h_pct * 100, 1),
            },
            "reasons": {
                "th": reasons_th,
                "en": reasons_en
            },
        })

    return positions_out


# ═══════════════════════════════════════════════════════════════════════════
#  Explainable AI Engine
# ═══════════════════════════════════════════════════════════════════════════

class ExplainableAI:

    def __init__(self, csv_path: str | Path = CSV_PATH):
        self.csv_path = Path(csv_path)
        self.rows: list[dict] = []
        self.explanations: list[dict] = []

    def load(self) -> "ExplainableAI":
        self.rows = load_rows(self.csv_path)
        print(f"[INFO] Loaded {len(self.rows)} draws")
        return self

    def explain(self, number: str) -> dict:
        """Generate full explanation for a single 6-digit candidate."""
        number = number.strip().zfill(6)[:6]
        position_details = _compute_factor_scores(self.rows, number)

        # Overall factor scores (sum across positions)
        total_pattern = sum(p["factor_scores"]["pattern_score"] for p in position_details)
        total_prob    = sum(p["factor_scores"]["probability_score"] for p in position_details)
        total_heat    = sum(p["factor_scores"]["heatmap_score"] for p in position_details)
        grand_total   = total_pattern + total_prob + total_heat

        return {
            "number": number,
            "overall_factor_scores": {
                "pattern_score":     round(total_pattern, 5),
                "probability_score": round(total_prob, 5),
                "heatmap_score":     round(total_heat, 5),
                "grand_total":       round(grand_total, 5),
            },
            "overall_factor_pct": {
                "pattern_pct":     round(total_pattern / grand_total * 100, 1) if grand_total else 0,
                "probability_pct": round(total_prob    / grand_total * 100, 1) if grand_total else 0,
                "heatmap_pct":     round(total_heat    / grand_total * 100, 1) if grand_total else 0,
            },
            "positions": position_details,
            "explained_at": datetime.now().isoformat(),
        }

    def explain_candidates(self, top_k: int = 5) -> list[dict]:
        """Pull top candidates from ensemble predictor and explain each."""
        sys.path.insert(0, str(BASE_DIR))
        from ensemble_model.predictor import EnsemblePredictor
        predictor = EnsemblePredictor(self.csv_path)
        candidates = predictor.run(top_k=top_k, beam_width=3)

        self.explanations = []
        for cand in candidates:
            num = cand["number"]
            print(f"[INFO] Explaining candidate {num}…")
            exp = self.explain(num)
            exp["ensemble_confidence"] = cand.get("confidence", 0)
            exp["ensemble_score"] = cand.get("score", 0)
            self.explanations.append(exp)

        return self.explanations

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.explanations, ensure_ascii=False, indent=indent, default=str)

    def print_summary(self) -> None:
        if not self.explanations:
            print("[WARN] No explanations — call explain_candidates() first")
            return

        print("\n" + "=" * 64)
        print("  🔍 EXPLAINABLE AI — PREDICTION BREAKDOWN")
        print("=" * 64)

        for rank, exp in enumerate(self.explanations, 1):
            num = exp["number"]
            conf = exp.get("ensemble_confidence", 0)
            of = exp["overall_factor_pct"]

            print(f"\n  ┌─ #{rank}  {num}  (confidence: {conf:.1f}%) {'─'*30}")
            print(f"  │  Overall factors:")
            print(f"  │    📊 Probability  : {of['probability_pct']:>5.1f}%")
            print(f"  │    🌡  Heatmap      : {of['heatmap_pct']:>5.1f}%")
            print(f"  │    🔎 Pattern      : {of['pattern_pct']:>5.1f}%")
            print(f"  │")

            for pos in exp["positions"]:
                col = pos["position"]
                d   = pos["digit"]
                fc  = pos["factor_contribution"]
                bar_p  = "█" * int(fc["probability_pct"] / 10)
                bar_h  = "█" * int(fc["heatmap_pct"] / 10)
                bar_pt = "█" * int(fc["pattern_pct"] / 10)

                print(f"  │  {col} = {d}")
                print(f"  │    Prob {fc['probability_pct']:>5.1f}% {bar_p}")
                print(f"  │    Heat {fc['heatmap_pct']:>5.1f}% {bar_h}")
                print(f"  │    Patt {fc['pattern_pct']:>5.1f}% {bar_pt}")

                for reason in pos["reasons"]["th"]:
                    print(f"  │    → {reason}")

            print(f"  └{'─'*60}")

        print("\n" + "=" * 64)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Explainable AI for Lottery Predictions")
    parser.add_argument("--number", type=str, default="",   help="Explain a specific 6-digit number")
    parser.add_argument("--top",    type=int, default=3,    help="Top-K candidates to explain")
    parser.add_argument("--json",   action="store_true",    help="Print JSON output")
    parser.add_argument("--save",   type=str, default="",   help="Save JSON to file")
    args = parser.parse_args()

    xai = ExplainableAI()
    xai.load()

    if args.number:
        exp = xai.explain(args.number)
        xai.explanations = [exp]
    else:
        xai.explain_candidates(top_k=args.top)

    if args.json:
        print(xai.to_json())
    else:
        xai.print_summary()

    if args.save:
        p = Path(args.save)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(xai.to_json(), encoding="utf-8")
        print(f"\n[INFO] Saved → {p}")


if __name__ == "__main__":
    main()
