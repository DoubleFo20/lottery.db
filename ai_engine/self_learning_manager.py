"""
Self-Learning Manager
======================
Automatic AI self-improvement orchestrator.

Feedback loop:
  New draw result
  → Evaluate prediction accuracy
  → Update performance metrics
  → Apply improvement rules
  → Adjust strategy weights
  → Generate improved prediction model

Integrates with:
  - analytics/prediction_history.py
  - analytics/performance_analyzer.py
  - ai_engine/self_learning.py
  - ensemble_model/predictor.py

Output:
  analytics/model_adjustments.json

Usage:
  python ai_engine/self_learning_manager.py --run           # full feedback loop
  python ai_engine/self_learning_manager.py --evaluate-only # assess without adjusting
  python ai_engine/self_learning_manager.py --status        # print current system status
  python ai_engine/self_learning_manager.py --json          # JSON output
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import json
import math
import sys
from collections import Counter
from copy import deepcopy
from datetime import datetime
from pathlib import Path

# ───────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

HISTORY_JSON    = BASE_DIR / "database" / "predictions" / "prediction_history.json"
PERF_JSON       = BASE_DIR / "performance.json"
ADJ_LOG         = BASE_DIR / "analytics" / "model_adjustments.json"
WEIGHT_FILE     = BASE_DIR / "database" / "predictions" / "ensemble_weights.json"
CSV_PATH        = BASE_DIR / "database" / "dataset" / "lottery_history.csv"

EVAL_WINDOWS    = [50, 100, 200]

DEFAULT_WEIGHTS = {
    "positional_freq":  0.20,
    "rolling_heat":     0.20,
    "conditional":      0.15,
    "transition":       0.10,
    "pair_lift":        0.10,
    "pattern_hot":      0.10,
    "gap_overdue":      0.08,
    "temporal_trend":   0.07,
}

LEARNING_RATE   = 0.025
MIN_WEIGHT      = 0.02
MAX_WEIGHT      = 0.40

# ═══════════════════════════════════════════════════════════════════════════
#  IO
# ═══════════════════════════════════════════════════════════════════════════

def _load_json(path: Path):
    if path.exists() and path.stat().st_size > 0:
        return json.loads(path.read_text(encoding="utf-8"))
    return None

def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )

def _load_weights() -> dict:
    w = _load_json(WEIGHT_FILE)
    if isinstance(w, dict) and w:
        return w
    return dict(DEFAULT_WEIGHTS)


# ═══════════════════════════════════════════════════════════════════════════
#  1. Gather Metrics — multi-window evaluation
# ═══════════════════════════════════════════════════════════════════════════

def _gather_metrics() -> dict:
    """
    Pull evaluated predictions from history, compute per-window
    and overall accuracy metrics.
    """
    raw = _load_json(HISTORY_JSON)
    if not isinstance(raw, list):
        raw = []

    evaluated = [e for e in raw if e.get("accuracy")]
    n = len(evaluated)

    def _window_metrics(entries: list) -> dict:
        if not entries:
            return {"count": 0}
        pos_list = [e["accuracy"]["best"].get("positional_hits", 0) for e in entries]
        dig_list = [e["accuracy"]["best"].get("digit_hits", 0)      for e in entries]
        exact    = sum(1 for e in entries if e["accuracy"].get("any_exact_match"))
        avg_pos  = sum(pos_list) / len(pos_list)
        avg_dig  = sum(dig_list) / len(dig_list)

        # position accuracy per-position
        pos_acc = [0]*6
        pos_tot = [0]*6
        for e in entries:
            actual = e.get("actual_result", "")
            best_c = e["accuracy"]["best"].get("candidate", "")
            if len(actual) == 6 and len(best_c) == 6:
                for i in range(6):
                    pos_tot[i] += 1
                    if best_c[i] == actual[i]:
                        pos_acc[i] += 1

        per_pos = {}
        for i in range(6):
            per_pos[f"digit{i+1}"] = round(pos_acc[i] / pos_tot[i] * 100, 2) if pos_tot[i] else 0

        sigma = 0
        if len(pos_list) > 1:
            sigma = math.sqrt(sum((x - avg_pos)**2 for x in pos_list) / len(pos_list))
        consistency = max(0, 1 - sigma / 6)

        return {
            "count":            len(entries),
            "avg_pos_hits":     round(avg_pos, 3),
            "avg_dig_hits":     round(avg_dig, 3),
            "exact_matches":    exact,
            "consistency":      round(consistency, 4),
            "position_accuracy": per_pos,
        }

    # Overall + windowed
    metrics = {"overall": _window_metrics(evaluated)}
    for w in EVAL_WINDOWS:
        metrics[f"window_{w}"] = _window_metrics(evaluated[-w:])

    # Model score from performance.json
    perf = _load_json(PERF_JSON)
    if isinstance(perf, dict):
        ms = perf.get("model_score", {})
        metrics["model_score"]  = ms.get("score", 0)
        metrics["model_grade"]  = ms.get("grade", "?")
    else:
        metrics["model_score"] = 0
        metrics["model_grade"] = "N/A"

    metrics["total_evaluated"] = n
    return metrics


# ═══════════════════════════════════════════════════════════════════════════
#  2. Strategy Ranking
# ═══════════════════════════════════════════════════════════════════════════

def _rank_strategies(metrics: dict) -> list[dict]:
    """
    Rank signal strategies by effectiveness.
    """
    weights = _load_weights()
    overall = metrics.get("overall", {})
    avg_dig = overall.get("avg_dig_hits", 0)
    model_s = metrics.get("model_score", 0)

    strategies = [
        {
            "name": "Hot Digit Strategy",
            "signals": ["pattern_hot", "rolling_heat"],
            "weight_sum": sum(weights.get(s, 0) for s in ["pattern_hot", "rolling_heat"]),
            "description": "Based on digits currently trending above average",
        },
        {
            "name": "Probability Model",
            "signals": ["positional_freq", "conditional", "pair_lift"],
            "weight_sum": sum(weights.get(s, 0) for s in ["positional_freq", "conditional", "pair_lift"]),
            "description": "Statistical positional frequency + conditional probability",
        },
        {
            "name": "Trend Pattern Strategy",
            "signals": ["temporal_trend", "gap_overdue"],
            "weight_sum": sum(weights.get(s, 0) for s in ["temporal_trend", "gap_overdue"]),
            "description": "Temporal trends + overdue digit recovery",
        },
        {
            "name": "Transition Model",
            "signals": ["transition"],
            "weight_sum": weights.get("transition", 0),
            "description": "Draw-to-draw digit transition probability",
        },
    ]

    # Approximate effectiveness: weight_sum * (avg_dig / 6) as proxy
    effectiveness = avg_dig / 6 if avg_dig else 0.1
    for st in strategies:
        st["effectiveness_score"] = round(st["weight_sum"] * effectiveness * 100, 2)

    # Random baseline
    strategies.append({
        "name": "Random Baseline",
        "signals": [],
        "weight_sum": 0,
        "description": "Random selection (baseline comparison)",
        "effectiveness_score": round(10.0 * 1.67 / 6 * 100, 2),  # chance
    })

    strategies.sort(key=lambda s: s["effectiveness_score"], reverse=True)
    for i, st in enumerate(strategies, 1):
        st["rank"] = i

    return strategies


# ═══════════════════════════════════════════════════════════════════════════
#  3. Improvement Rules Engine
# ═══════════════════════════════════════════════════════════════════════════

def _apply_rules(metrics: dict, weights: dict) -> tuple[dict, list[dict]]:
    """
    Apply improvement rules based on current metrics.
    Returns (adjusted_weights, actions_taken).
    """
    new_w = deepcopy(weights)
    actions = []

    score     = metrics.get("model_score", 0)
    n_eval    = metrics.get("total_evaluated", 0)
    overall   = metrics.get("overall", {})
    avg_dig   = overall.get("avg_dig_hits", 0)
    avg_pos   = overall.get("avg_pos_hits", 0)
    consist   = overall.get("consistency", 0)
    pos_acc   = overall.get("position_accuracy", {})

    # ── Rule 1: Score < 50, ≥ 50 evaluated → nudge weights ──
    if score < 50 and n_eval >= 50:
        # Boost probability signals
        for sig in ["positional_freq", "conditional"]:
            new_w[sig] = min(MAX_WEIGHT, new_w.get(sig, 0.1) + LEARNING_RATE)
        # Reduce weakest
        weakest = min(new_w, key=new_w.get)
        new_w[weakest] = max(MIN_WEIGHT, new_w[weakest] - LEARNING_RATE)
        actions.append({
            "rule": "LOW_SCORE_WEIGHT_NUDGE",
            "trigger": f"model_score={score} < 50 and evaluated={n_eval} ≥ 50",
            "action": f"Boosted positional_freq, conditional; reduced {weakest}",
            "severity": "medium",
        })

    # ── Rule 2: Score < 40, ≥ 150 evaluated → aggressive rebuild ──
    if score < 40 and n_eval >= 150:
        # Reset toward probability-heavy baseline
        new_w["positional_freq"]  = 0.25
        new_w["rolling_heat"]     = 0.20
        new_w["conditional"]      = 0.18
        new_w["transition"]       = 0.10
        new_w["pair_lift"]        = 0.10
        new_w["pattern_hot"]      = 0.07
        new_w["gap_overdue"]      = 0.05
        new_w["temporal_trend"]   = 0.05
        actions.append({
            "rule": "CRITICAL_SCORE_REBUILD",
            "trigger": f"model_score={score} < 40 and evaluated={n_eval} ≥ 150",
            "action": "Reset to probability-heavy baseline weights",
            "severity": "high",
        })

    # ── Rule 3: Digit accuracy improving → reward probability ──
    w50  = metrics.get("window_50", {})
    w100 = metrics.get("window_100", {})
    if (w50.get("count", 0) >= 10 and w100.get("count", 0) >= 20
            and w50.get("avg_dig_hits", 0) > w100.get("avg_dig_hits", 0)):
        new_w["positional_freq"] = min(MAX_WEIGHT, new_w.get("positional_freq", 0.2) + 0.01)
        new_w["pair_lift"]       = min(MAX_WEIGHT, new_w.get("pair_lift", 0.1) + 0.01)
        actions.append({
            "rule": "DIGIT_ACCURACY_IMPROVING",
            "trigger": f"50-draw avg {w50['avg_dig_hits']:.2f} > 100-draw avg {w100['avg_dig_hits']:.2f}",
            "action": "Increased positional_freq and pair_lift weights",
            "severity": "low",
        })

    # ── Rule 4: Poor positional consistency → boost transition ──
    if consist < 0.5 and n_eval >= 30:
        new_w["transition"]   = min(MAX_WEIGHT, new_w.get("transition", 0.1) + LEARNING_RATE)
        new_w["rolling_heat"] = min(MAX_WEIGHT, new_w.get("rolling_heat", 0.2) + 0.01)
        actions.append({
            "rule": "LOW_CONSISTENCY_BOOST",
            "trigger": f"consistency={consist:.2f} < 0.5 and n={n_eval}",
            "action": "Boosted transition and rolling_heat for stability",
            "severity": "medium",
        })

    # ── Rule 5: If specific positions are weak → recommend focus ──
    weak_positions = [p for p, acc in pos_acc.items() if acc < 5 and n_eval >= 20]
    if weak_positions:
        actions.append({
            "rule": "WEAK_POSITIONS_DETECTED",
            "trigger": f"Positions with <5% accuracy: {', '.join(weak_positions)}",
            "action": "Consider per-position model tuning for these slots",
            "severity": "info",
        })

    # ── Rule 6: Evaluate < 50 → recommend more data ──
    if n_eval < 50:
        actions.append({
            "rule": "INSUFFICIENT_DATA",
            "trigger": f"Only {n_eval} draws evaluated (min recommended: 50)",
            "action": "Continue logging predictions and recording actuals to build history",
            "severity": "info",
        })

    # ── Rule 7: Gap overdue low contribution → can reduce ──
    if n_eval >= 50 and avg_pos < 0.5:
        new_w["gap_overdue"] = max(MIN_WEIGHT, new_w.get("gap_overdue", 0.08) - 0.01)
        actions.append({
            "rule": "OVERDUE_SIGNAL_WEAK",
            "trigger": f"avg_pos={avg_pos:.2f} very low, gap_overdue may add noise",
            "action": "Reduced gap_overdue weight slightly",
            "severity": "low",
        })

    # Normalise
    total = sum(new_w.values())
    if total > 0:
        new_w = {k: round(v / total, 5) for k, v in new_w.items()}

    if not actions:
        actions.append({
            "rule": "NO_ADJUSTMENT_NEEDED",
            "trigger": "All metrics within acceptable range",
            "action": "No weight changes applied",
            "severity": "info",
        })

    return new_w, actions


# ═══════════════════════════════════════════════════════════════════════════
#  4. Recommendations Generator
# ═══════════════════════════════════════════════════════════════════════════

def _generate_recommendations(metrics: dict, strategies: list, actions: list) -> list[dict]:
    recs = []
    score  = metrics.get("model_score", 0)
    n_eval = metrics.get("total_evaluated", 0)

    if n_eval < 50:
        recs.append({
            "priority": "HIGH",
            "title": "Increase Dataset",
            "detail": f"Only {n_eval} draws evaluated. Need ≥50 for reliable adjustments. "
                      "Run: python analytics/prediction_history.py --log after each draw."
        })

    if score < 40:
        recs.append({
            "priority": "HIGH",
            "title": "Rebuild Model Weights",
            "detail": "Model score critically low. Consider running full self-learning cycle: "
                      "python ai_engine/self_learning.py --auto"
        })
    elif score < 60:
        recs.append({
            "priority": "MEDIUM",
            "title": "Adjust Probability Weights",
            "detail": "Model score below target. The system has applied automatic adjustments."
        })

    # Disable weak strategies
    bottom = [s for s in strategies if s["rank"] >= len(strategies) - 1
              and s["name"] != "Random Baseline"]
    for s in bottom:
        recs.append({
            "priority": "LOW",
            "title": f"Review Strategy: {s['name']}",
            "detail": f"Effectiveness score {s['effectiveness_score']} — "
                      "consider reducing weight of signals: " + ", ".join(s["signals"])
        })

    if not recs:
        recs.append({
            "priority": "OK",
            "title": "System Healthy",
            "detail": "All indicators within acceptable range. Continue monitoring."
        })

    return recs


# ═══════════════════════════════════════════════════════════════════════════
#  5. Main Feedback Loop
# ═══════════════════════════════════════════════════════════════════════════

class SelfLearningManager:

    def __init__(self):
        self.metrics:        dict      = {}
        self.strategies:     list      = []
        self.old_weights:    dict      = {}
        self.new_weights:    dict      = {}
        self.actions:        list      = []
        self.recommendations: list     = []
        self.result:         dict      = {}

    def run(self, apply_changes: bool = True) -> dict:
        """Execute the full feedback loop."""

        # Step 1: Gather metrics
        print("[STEP 1/5] Gathering performance metrics…")
        self.metrics = _gather_metrics()

        # Step 2: Rank strategies
        print("[STEP 2/5] Ranking strategies…")
        self.strategies = _rank_strategies(self.metrics)

        # Step 3: Apply improvement rules
        print("[STEP 3/5] Applying improvement rules…")
        self.old_weights = _load_weights()
        self.new_weights, self.actions = _apply_rules(self.metrics, self.old_weights)

        # Step 4: Generate recommendations
        print("[STEP 4/5] Generating recommendations…")
        self.recommendations = _generate_recommendations(
            self.metrics, self.strategies, self.actions)

        # Step 5: Save
        print("[STEP 5/5] Saving results…")
        if apply_changes:
            _save_json(WEIGHT_FILE, self.new_weights)

        self.result = {
            "timestamp":       datetime.now().isoformat(),
            "model_score":     self.metrics.get("model_score", 0),
            "model_grade":     self.metrics.get("model_grade", "?"),
            "total_evaluated": self.metrics.get("total_evaluated", 0),
            "evaluation_windows": {
                k: v for k, v in self.metrics.items()
                if k.startswith("window_") or k == "overall"
            },
            "old_weights":     self.old_weights,
            "new_weights":     self.new_weights,
            "weight_changes":  {
                k: round(self.new_weights.get(k, 0) - self.old_weights.get(k, 0), 5)
                for k in set(list(self.old_weights) + list(self.new_weights))
            },
            "actions_applied":  self.actions,
            "strategy_ranking": self.strategies,
            "recommendations":  self.recommendations,
            "changes_applied":  apply_changes,
        }

        # Append to adjustment log
        log = _load_json(ADJ_LOG)
        if not isinstance(log, list):
            log = []
        log.append(self.result)
        _save_json(ADJ_LOG, log)

        return self.result

    # ─── Reports ────────────────────────────────────
    def to_json(self) -> str:
        return json.dumps(self.result, ensure_ascii=False, indent=2, default=str)

    def print_report(self):
        r = self.result
        if not r:
            print("[WARN] No results — run first")
            return

        print("\n" + "=" * 64)
        print("  🧠 AI SELF-LEARNING MANAGER — FEEDBACK REPORT")
        print("=" * 64)

        # ── Score & Grade ──
        score = r["model_score"]
        grade = r["model_grade"]
        icon  = "🟢" if score >= 60 else ("🟡" if score >= 30 else "🔴")
        print(f"\n  {icon} Model Score: {score} / 100  Grade: {grade}")
        print(f"  📊 Draws Evaluated: {r['total_evaluated']}")

        # ── Evaluation Windows ──
        print(f"\n─── 📐 EVALUATION WINDOWS ───────────────────────")
        for key, val in r.get("evaluation_windows", {}).items():
            if isinstance(val, dict) and val.get("count", 0) > 0:
                label = key.replace("window_", "Last ").replace("overall", "Overall")
                print(f"  {label:>12}: n={val['count']}  "
                      f"pos={val.get('avg_pos_hits', 0):.2f}/6  "
                      f"dig={val.get('avg_dig_hits', 0):.2f}/6  "
                      f"exact={val.get('exact_matches', 0)}  "
                      f"consistency={val.get('consistency', 0):.1%}")

        # ── Strategy Ranking ──
        print(f"\n─── 🏆 STRATEGY RANKING ─────────────────────────")
        for st in r.get("strategy_ranking", []):
            medal = "🥇🥈🥉"[st["rank"]-1] if st["rank"] <= 3 else "  "
            bar = "█" * int(st["effectiveness_score"] / 3)
            print(f"  {medal} #{st['rank']} {st['name']:<25} "
                  f"score={st['effectiveness_score']:>6.1f}  {bar}")

        # ── Actions ──
        print(f"\n─── ⚡ ACTIONS APPLIED ──────────────────────────")
        for a in r.get("actions_applied", []):
            sev = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(a["severity"], "•")
            print(f"  {sev} [{a['rule']}]")
            print(f"     Trigger: {a['trigger']}")
            print(f"     Action:  {a['action']}")

        # ── Weight Changes ──
        changes = r.get("weight_changes", {})
        if any(v != 0 for v in changes.values()):
            print(f"\n─── ⚖️ WEIGHT ADJUSTMENTS ──────────────────────")
            print(f"  {'Signal':<20} {'Old':>7} {'New':>7} {'Δ':>8}")
            print(f"  {'─'*20} {'─'*7} {'─'*7} {'─'*8}")
            for sig in sorted(changes, key=lambda x: abs(changes[x]), reverse=True):
                old = r["old_weights"].get(sig, 0)
                new = r["new_weights"].get(sig, 0)
                d   = changes[sig]
                arrow = "↑" if d > 0 else ("↓" if d < 0 else "=")
                print(f"  {sig:<20} {old:>6.1%} {new:>6.1%} {d:>+7.2%} {arrow}")

        # ── Recommendations ──
        print(f"\n─── 💡 RECOMMENDATIONS ─────────────────────────")
        for rec in r.get("recommendations", []):
            pri = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "OK": "✅"}.get(rec["priority"], "•")
            print(f"  {pri} {rec['title']}")
            print(f"     {rec['detail']}")

        print("\n" + "=" * 64)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="AI Self-Learning Manager")
    parser.add_argument("--run",           action="store_true", help="Full feedback loop (evaluate + adjust + save)")
    parser.add_argument("--evaluate-only", action="store_true", help="Evaluate only, do not apply changes")
    parser.add_argument("--status",        action="store_true", help="Print current system status")
    parser.add_argument("--json",          action="store_true", help="Output JSON")
    args = parser.parse_args()

    mgr = SelfLearningManager()

    if args.evaluate_only:
        mgr.run(apply_changes=False)
    else:
        mgr.run(apply_changes=True)

    if args.json:
        print(mgr.to_json())
    else:
        mgr.print_report()


if __name__ == "__main__":
    main()
