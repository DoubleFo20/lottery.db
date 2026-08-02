"""
Prediction History Logger
==========================
Records every prediction run to a persistent CSV and JSON log.

Stores:
  - Timestamp
  - Predicted candidates (numbers + confidence)
  - Actual result (if known)
  - Accuracy metrics (if actual provided)

Output:
  database/predictions/prediction_history.csv
  database/predictions/prediction_history.json

Usage:
  python analytics/prediction_history.py --log           # log latest pipeline cache
  python analytics/prediction_history.py --actual 219367 --date 2026-04-01  # record result
  python analytics/prediction_history.py --report        # show history summary
  python analytics/prediction_history.py --export        # export full JSON
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
BASE_DIR      = Path(__file__).resolve().parents[1]
CACHE_PATH    = BASE_DIR / "database" / "predictions" / "pipeline_cache.json"
HISTORY_CSV   = BASE_DIR / "database" / "predictions" / "prediction_history.csv"
HISTORY_JSON  = BASE_DIR / "database" / "predictions" / "prediction_history.json"

CSV_FIELDS = [
    "logged_at", "target_date", "draw_date_used",
    "rank1_number", "rank1_confidence",
    "rank2_number", "rank2_confidence",
    "rank3_number", "rank3_confidence",
    "rank4_number", "rank4_confidence",
    "rank5_number", "rank5_confidence",
    "actual_result",
    "exact_match",
    "best_positional_hits",
    "best_digit_hits",
    "note",
]


# ═══════════════════════════════════════════════════════════════════════════
#  IO Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _ensure_dir():
    HISTORY_CSV.parent.mkdir(parents=True, exist_ok=True)


def _load_json_log() -> list[dict]:
    if HISTORY_JSON.exists() and HISTORY_JSON.stat().st_size > 0:
        return json.loads(HISTORY_JSON.read_text(encoding="utf-8"))
    return []


def _save_json_log(entries: list[dict]):
    _ensure_dir()
    HISTORY_JSON.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )


def _append_csv(row: dict):
    _ensure_dir()
    write_header = not HISTORY_CSV.exists() or HISTORY_CSV.stat().st_size == 0
    with open(HISTORY_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def _load_cache() -> dict | None:
    if not CACHE_PATH.exists():
        print(f"[WARN] No pipeline cache: {CACHE_PATH}")
        return None
    return json.loads(CACHE_PATH.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════════════════════
#  Accuracy Scorer
# ═══════════════════════════════════════════════════════════════════════════

def _score(predicted: str, actual: str) -> dict:
    p = list(predicted.zfill(6)[:6])
    a = list(actual.zfill(6)[:6])
    pos_hits = sum(1 for i in range(6) if p[i] == a[i])
    pool = list(a)
    dh = 0
    for d in p:
        if d in pool:
            dh += 1
            pool.remove(d)
    return {
        "exact_match":       predicted == actual,
        "positional_hits":   pos_hits,
        "digit_hits":        dh,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  1. Log Prediction
# ═══════════════════════════════════════════════════════════════════════════

def log_prediction(target_date: str = "", note: str = "") -> dict:
    """Log the current pipeline cache as a new prediction entry."""
    cache = _load_cache()
    if not cache:
        return {}

    candidates = cache.get("candidates", [])
    last_draw  = cache.get("last_draw", {})
    now        = datetime.now().isoformat()

    # Build entry
    entry = {
        "logged_at":       now,
        "target_date":     target_date,
        "draw_date_used":  last_draw.get("date", "?"),
        "last_draw_number": last_draw.get("number", "?"),
        "candidates":      candidates,
        "actual_result":   None,
        "accuracy":        None,
        "note":            note,
    }

    # Dict row for CSV
    csv_row = {
        "logged_at":      now,
        "target_date":    target_date,
        "draw_date_used": last_draw.get("date", "?"),
        "actual_result":  "",
        "exact_match":    "",
        "best_positional_hits": "",
        "best_digit_hits": "",
        "note":           note,
    }
    for idx, cand in enumerate(candidates[:5], 1):
        csv_row[f"rank{idx}_number"]     = cand.get("number", "")
        csv_row[f"rank{idx}_confidence"] = cand.get("confidence", 0)

    # Save
    log_data = _load_json_log()
    log_data.append(entry)
    _save_json_log(log_data)
    _append_csv(csv_row)

    print(f"[OK] Logged prediction — {len(candidates)} candidates for {target_date or 'unspecified date'}")
    for c in candidates:
        print(f"     {c['number']}  ({c['confidence']:.1f}%)")

    return entry


# ═══════════════════════════════════════════════════════════════════════════
#  2. Record Actual Result
# ═══════════════════════════════════════════════════════════════════════════

def record_actual(actual_number: str, target_date: str) -> dict | None:
    """
    Find the most recent prediction for `target_date` and record
    the actual lottery result, computing accuracy metrics.
    """
    log_data = _load_json_log()
    if not log_data:
        print("[WARN] No prediction history")
        return None

    # Find matching entry (exact date or latest)
    match = None
    for entry in reversed(log_data):
        if not entry.get("target_date") or entry["target_date"] == target_date:
            match = entry
            break

    if not match:
        print(f"[WARN] No entry found for date {target_date}")
        return None

    candidates = match.get("candidates", [])
    accuracy_list = []
    for cand in candidates:
        sc = _score(cand["number"], actual_number)
        sc["candidate"] = cand["number"]
        sc["confidence"] = cand.get("confidence", 0)
        accuracy_list.append(sc)

    best = max(accuracy_list, key=lambda x: x["positional_hits"]) if accuracy_list else {}

    match["actual_result"] = actual_number
    match["accuracy"] = {
        "per_candidate":       accuracy_list,
        "best":                best,
        "any_exact_match":     any(a["exact_match"] for a in accuracy_list),
        "avg_positional_hits": round(sum(a["positional_hits"] for a in accuracy_list) / len(accuracy_list), 2) if accuracy_list else 0,
        "avg_digit_hits":      round(sum(a["digit_hits"]      for a in accuracy_list) / len(accuracy_list), 2) if accuracy_list else 0,
    }

    _save_json_log(log_data)

    # Update CSV — re-read + rewrite matching row
    if HISTORY_CSV.exists():
        rows = []
        with open(HISTORY_CSV, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["logged_at"] == match["logged_at"]:
                    row["actual_result"] = actual_number
                    row["exact_match"]   = str(match["accuracy"]["any_exact_match"])
                    row["best_positional_hits"] = best.get("positional_hits", 0)
                    row["best_digit_hits"]      = best.get("digit_hits", 0)
                rows.append(row)
        with open(HISTORY_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    print(f"[OK] Recorded actual result: {actual_number} for {target_date}")
    print(f"     Best candidate: {best.get('candidate', '?')}  pos={best.get('positional_hits', 0)}/6  dig={best.get('digit_hits', 0)}/6")
    if match["accuracy"].get("any_exact_match"):
        print("     🎉 EXACT MATCH!")
    return match


# ═══════════════════════════════════════════════════════════════════════════
#  3. Report
# ═══════════════════════════════════════════════════════════════════════════

def print_report():
    log_data = _load_json_log()
    if not log_data:
        print("[WARN] No prediction history — run --log first")
        return

    evaluated = [e for e in log_data if e.get("accuracy")]
    pending   = [e for e in log_data if not e.get("accuracy")]

    print("\n" + "=" * 60)
    print("  📜 PREDICTION HISTORY REPORT")
    print("=" * 60)
    print(f"  Total logged    : {len(log_data)}")
    print(f"  Evaluated       : {len(evaluated)}")
    print(f"  Pending result  : {len(pending)}")

    if evaluated:
        all_pos = [e["accuracy"]["avg_positional_hits"] for e in evaluated]
        all_dig = [e["accuracy"]["avg_digit_hits"]      for e in evaluated]
        exact   = sum(1 for e in evaluated if e["accuracy"].get("any_exact_match"))

        print(f"\n  Avg pos hits    : {sum(all_pos)/len(all_pos):.2f} / 6")
        print(f"  Avg digit hits  : {sum(all_dig)/len(all_dig):.2f} / 6")
        print(f"  Exact matches   : {exact}")

        print(f"\n─── EVALUATED PREDICTIONS ───────────────────────")
        for e in evaluated[-10:]:  # last 10
            acc  = e["accuracy"]
            best = acc.get("best", {})
            mark = "🎉" if acc.get("any_exact_match") else "  "
            print(f"  {mark} {e.get('target_date','?'):<12}  actual={e.get('actual_result','?')}  "
                  f"best={best.get('candidate','?')}  "
                  f"pos={best.get('positional_hits',0)}/6  "
                  f"dig={best.get('digit_hits',0)}/6")

    print(f"\n─── PENDING PREDICTIONS ─────────────────────────")
    for e in pending[-5:]:
        cands = [c["number"] for c in e.get("candidates", [])[:3]]
        print(f"  {e.get('target_date','?'):<12}  logged={e['logged_at'][:16]}  top={cands}")

    print("\n" + "=" * 60)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Prediction History Logger")
    parser.add_argument("--log",    action="store_true", help="Log current pipeline cache")
    parser.add_argument("--actual", type=str, default="", help="Record actual result (6 digits)")
    parser.add_argument("--date",   type=str, default="", help="Target draw date (YYYY-MM-DD)")
    parser.add_argument("--note",   type=str, default="", help="Optional note")
    parser.add_argument("--report", action="store_true", help="Show history summary")
    parser.add_argument("--export", action="store_true", help="Print full JSON")
    args = parser.parse_args()

    if args.log:
        log_prediction(target_date=args.date, note=args.note)
    elif args.actual:
        if not args.date:
            print("[ERROR] --date YYYY-MM-DD is required when recording actual result")
        else:
            record_actual(args.actual, args.date)
    elif args.export:
        data = _load_json_log()
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        print_report()


if __name__ == "__main__":
    main()
