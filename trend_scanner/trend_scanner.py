"""
Trend Scanner
==============
Scans lottery history for emerging trends in real-time windows.

Input:  database/dataset/lottery_history.csv
Cols:   draw_date, digit1 … digit6

Detects:
  1. Digit Streaks        — same digit repeating consecutively at a position
  2. Frequency Spikes     — sudden rise above rolling baseline
  3. Recent Patterns      — 2/3-digit sequences surging in latest window

Output: terminal report + optional JSON

Usage:
  python trend_scanner/trend_scanner.py
  python trend_scanner/trend_scanner.py --window 20
  python trend_scanner/trend_scanner.py --json
  python trend_scanner/trend_scanner.py --save trends.json
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
BASE_DIR   = Path(__file__).resolve().parents[1]
CSV_PATH   = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
DIGIT_COLS = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]
ALL_DIGITS = [str(d) for d in range(10)]

SPIKE_THRESHOLD  = 1.5   # freq_recent / freq_baseline > this → spike
STREAK_MIN_LEN   = 2     # minimum consecutive matches to report


# ═══════════════════════════════════════════════════════════════════════════
#  Data loading
# ═══════════════════════════════════════════════════════════════════════════

def load(path: Path) -> list[dict]:
    if not path.exists():
        print(f"[ERROR] Not found: {path}", file=sys.stderr)
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if all(row.get(c, "").isdigit() for c in DIGIT_COLS):
                rows.append(row)
    print(f"[INFO] Loaded {len(rows)} draws")
    return rows


# ═══════════════════════════════════════════════════════════════════════════
#  1. Digit Streaks
# ═══════════════════════════════════════════════════════════════════════════

def detect_streaks(rows: list[dict]) -> list[dict]:
    """
    Find all positions where the same digit appeared consecutively
    across multiple draws (minimum STREAK_MIN_LEN).

    Rows are in descending date order, so we scan forward for streaks
    starting from the most recent draw.
    """
    streaks = []

    for col in DIGIT_COLS:
        # Walk draws newest-first
        current_digit = None
        streak_len    = 0
        streak_start_idx = 0

        for idx, row in enumerate(rows):
            d = row[col]
            if d == current_digit:
                streak_len += 1
            else:
                if streak_len >= STREAK_MIN_LEN:
                    streaks.append({
                        "position":    col,
                        "digit":       current_digit,
                        "length":      streak_len,
                        "start_date":  rows[streak_start_idx].get("draw_date", "?"),
                        "end_date":    rows[idx - 1].get("draw_date", "?"),
                        "active":      streak_start_idx == 0,  # still ongoing?
                    })
                current_digit     = d
                streak_len        = 1
                streak_start_idx  = idx

        # flush last
        if streak_len >= STREAK_MIN_LEN:
            streaks.append({
                "position":   col,
                "digit":      current_digit,
                "length":     streak_len,
                "start_date": rows[streak_start_idx].get("draw_date", "?"),
                "end_date":   rows[len(rows) - 1].get("draw_date", "?"),
                "active":     streak_start_idx == 0,
            })

    streaks.sort(key=lambda s: (s["active"], s["length"]), reverse=True)
    return streaks


# ═══════════════════════════════════════════════════════════════════════════
#  2. Frequency Spikes
# ═══════════════════════════════════════════════════════════════════════════

def detect_spikes(rows: list[dict], window: int = 20) -> list[dict]:
    """
    Compare digit frequency in the most recent `window` draws
    against the long-term baseline (full history).

    A spike is flagged when:
      freq_recent / freq_baseline > SPIKE_THRESHOLD
    A drop is flagged when:
      freq_baseline / freq_recent > SPIKE_THRESHOLD
    """
    if len(rows) < window + 1:
        return []

    recent   = rows[:window]
    baseline = rows[window:]

    spikes = []

    for col in DIGIT_COLS:
        recent_cnt   = Counter(r[col] for r in recent)
        baseline_cnt = Counter(r[col] for r in baseline)

        recent_total   = sum(recent_cnt.values())
        baseline_total = sum(baseline_cnt.values())

        for d in ALL_DIGITS:
            f_rec  = recent_cnt.get(d, 0) / recent_total   if recent_total   else 0
            f_base = baseline_cnt.get(d, 0) / baseline_total if baseline_total else 0.001

            ratio = f_rec / f_base if f_base else 0

            if ratio >= SPIKE_THRESHOLD:
                spikes.append({
                    "position":         col,
                    "digit":            d,
                    "type":             "🔺 SPIKE",
                    "recent_freq":      round(f_rec, 4),
                    "baseline_freq":    round(f_base, 4),
                    "ratio":            round(ratio, 2),
                    "recent_count":     recent_cnt.get(d, 0),
                    "baseline_count":   baseline_cnt.get(d, 0),
                })
            elif f_base > 0 and ratio > 0 and (1 / ratio) >= SPIKE_THRESHOLD and f_rec < f_base:
                spikes.append({
                    "position":         col,
                    "digit":            d,
                    "type":             "🔻 DROP",
                    "recent_freq":      round(f_rec, 4),
                    "baseline_freq":    round(f_base, 4),
                    "ratio":            round(ratio, 2),
                    "recent_count":     recent_cnt.get(d, 0),
                    "baseline_count":   baseline_cnt.get(d, 0),
                })

    spikes.sort(key=lambda s: abs(s["ratio"] - 1), reverse=True)
    return spikes


# ═══════════════════════════════════════════════════════════════════════════
#  3. Recent Pattern Surge
# ═══════════════════════════════════════════════════════════════════════════

def detect_recent_patterns(rows: list[dict], window: int = 20) -> dict:
    """
    Compares 2-digit and 3-digit sub-sequence frequencies between
    the recent window and the baseline — finds surging patterns.
    """
    if len(rows) < window + 1:
        return {}

    recent   = rows[:window]
    baseline = rows[window:]

    def count_subseqs(batch: list[dict], n: int) -> Counter:
        cnt = Counter()
        for row in batch:
            num = "".join(row[c] for c in DIGIT_COLS)
            for i in range(len(num) - n + 1):
                cnt[num[i:i + n]] += 1
        return cnt

    def top_surging(rec_cnt: Counter, base_cnt: Counter,
                    rec_total: int, base_total: int,
                    top_k: int = 8) -> list[dict]:
        results = []
        for seq in set(rec_cnt) | set(base_cnt):
            f_rec  = rec_cnt.get(seq, 0)  / rec_total   if rec_total   else 0
            f_base = base_cnt.get(seq, 0) / base_total  if base_total  else 0.001
            ratio  = f_rec / f_base if f_base else 0
            results.append({
                "sequence":       seq,
                "recent_count":   rec_cnt.get(seq, 0),
                "recent_freq":    round(f_rec, 4),
                "baseline_freq":  round(f_base, 4),
                "surge_ratio":    round(ratio, 2),
            })
        results.sort(key=lambda x: x["surge_ratio"], reverse=True)
        return results[:top_k]

    rec2  = count_subseqs(recent,   2);  base2  = count_subseqs(baseline, 2)
    rec3  = count_subseqs(recent,   3);  base3  = count_subseqs(baseline, 3)

    rt2 = sum(rec2.values());  bt2 = sum(base2.values())
    rt3 = sum(rec3.values());  bt3 = sum(base3.values())

    return {
        "top_surging_2digit": top_surging(rec2, base2, rt2, bt2),
        "top_surging_3digit": top_surging(rec3, base3, rt3, bt3),
        "top_dropping_2digit": sorted(
            top_surging(rec2, base2, rt2, bt2, top_k=999),
            key=lambda x: x["surge_ratio"]
        )[:5],
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Master Trend Scanner
# ═══════════════════════════════════════════════════════════════════════════

class TrendScanner:

    def __init__(self, csv_path: str | Path = CSV_PATH, window: int = 20):
        self.csv_path = Path(csv_path)
        self.window   = window
        self.rows:    list[dict] = []
        self.results: dict = {}

    def load(self) -> "TrendScanner":
        self.rows = load(self.csv_path)
        return self

    def scan(self) -> dict:
        if not self.rows:
            return {"error": "No data"}

        print("[INFO] Scanning digit streaks…")
        self.results["streaks"] = detect_streaks(self.rows)

        print("[INFO] Scanning frequency spikes…")
        self.results["spikes"] = detect_spikes(self.rows, self.window)

        print("[INFO] Scanning recent pattern surges…")
        self.results["recent_patterns"] = detect_recent_patterns(self.rows, self.window)

        # ── Trend summary for each digit ──
        spike_map: dict[str, dict[str, str]] = defaultdict(dict)
        for s in self.results["spikes"]:
            spike_map[s["digit"]][s["position"]] = s["type"]

        self.results["digit_trend_summary"] = {
            d: {
                "positions_spiking": [
                    pos for pos, typ in spike_map.get(d, {}).items() if "SPIKE" in typ
                ],
                "positions_dropping": [
                    pos for pos, typ in spike_map.get(d, {}).items() if "DROP" in typ
                ],
            }
            for d in ALL_DIGITS
        }

        self.results["meta"] = {
            "total_draws":    len(self.rows),
            "window":         self.window,
            "scanned_at":     datetime.now().isoformat(),
            "latest_draw":    self.rows[0].get("draw_date", "?") if self.rows else "?",
        }

        print(f"[INFO] Scan complete — "
              f"{len(self.results['streaks'])} streaks, "
              f"{len(self.results['spikes'])} spikes")
        return self.results

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.results, ensure_ascii=False, indent=indent, default=str)

    def print_report(self) -> None:
        r = self.results
        if "error" in r:
            print(f"\n⚠  {r['error']}")
            return

        meta = r["meta"]
        print("\n" + "=" * 62)
        print("  📡 TREND SCANNER REPORT")
        print("=" * 62)
        print(f"  Draws: {meta['total_draws']}   Window: {meta['window']}   Latest: {meta['latest_draw']}")

        # ── Streaks ──
        streaks = r.get("streaks", [])
        active  = [s for s in streaks if s["active"]]
        past    = [s for s in streaks if not s["active"]]

        print(f"\n─── 🔁 ACTIVE STREAKS (still going) ────────────────")
        if active:
            for s in active[:10]:
                print(f"  {s['position']}: digit {s['digit']} × {s['length']} draws  "
                      f"(from {s['start_date']})")
        else:
            print("  ไม่มี active streak ขณะนี้")

        print(f"\n─── 📜 HISTORICAL STREAKS (top 5) ──────────────────")
        for s in past[:5]:
            print(f"  {s['position']}: digit {s['digit']} × {s['length']} draws  "
                  f"({s['start_date']} → {s['end_date']})")

        # ── Spikes ──
        spikes = r.get("spikes", [])
        spike_up   = [s for s in spikes if "SPIKE" in s["type"]][:8]
        spike_down = [s for s in spikes if "DROP"  in s["type"]][:8]

        print(f"\n─── 🔺 FREQUENCY SPIKES (window={meta['window']}) ────────────")
        if spike_up:
            for s in spike_up:
                bar = "█" * min(int(s["ratio"] * 3), 20)
                print(f"  {s['position']} digit {s['digit']}: "
                      f"{s['recent_freq']*100:.1f}% now vs {s['baseline_freq']*100:.1f}% base  "
                      f"×{s['ratio']}  {bar}")
        else:
            print("  ไม่พบ spike ที่มีนัยสำคัญ")

        print(f"\n─── 🔻 FREQUENCY DROPS ──────────────────────────────")
        if spike_down:
            for s in spike_down:
                print(f"  {s['position']} digit {s['digit']}: "
                      f"{s['recent_freq']*100:.1f}% now vs {s['baseline_freq']*100:.1f}% base  "
                      f"×{s['ratio']}")
        else:
            print("  ไม่พบ drop ที่มีนัยสำคัญ")

        # ── Recent Patterns ──
        rp = r.get("recent_patterns", {})
        print(f"\n─── 📈 SURGING 2-DIGIT SEQUENCES ───────────────────")
        for seq in (rp.get("top_surging_2digit") or [])[:8]:
            bar = "█" * min(int(seq["surge_ratio"] * 3), 20)
            print(f"  '{seq['sequence']}' ×{seq['surge_ratio']}  "
                  f"({seq['recent_count']}x recent, {seq['recent_freq']*100:.1f}%)  {bar}")

        print(f"\n─── 📈 SURGING 3-DIGIT SEQUENCES ───────────────────")
        for seq in (rp.get("top_surging_3digit") or [])[:8]:
            bar = "█" * min(int(seq["surge_ratio"] * 2), 20)
            print(f"  '{seq['sequence']}' ×{seq['surge_ratio']}  "
                  f"({seq['recent_count']}x recent)  {bar}")

        # ── Digit summary ──
        print(f"\n─── 🔢 DIGIT TREND SUMMARY ──────────────────────────")
        dts = r.get("digit_trend_summary", {})
        for d in ALL_DIGITS:
            info = dts.get(d, {})
            up   = info.get("positions_spiking", [])
            down = info.get("positions_dropping", [])
            if up or down:
                tag = f"↑ {','.join(up)}" if up else ""
                tag += f"  ↓ {','.join(down)}" if down else ""
                print(f"  digit {d}: {tag.strip()}")

        print("\n" + "=" * 62)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Lottery Trend Scanner")
    parser.add_argument("--csv",    type=str, default=str(CSV_PATH))
    parser.add_argument("--window", type=int, default=20, help="Recent window size")
    parser.add_argument("--json",   action="store_true")
    parser.add_argument("--save",   type=str, default="")
    args = parser.parse_args()

    scanner = TrendScanner(args.csv, args.window)
    scanner.load().scan()

    if args.json:
        print(scanner.to_json())
    else:
        scanner.print_report()

    if args.save:
        p = Path(args.save)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(scanner.to_json(), encoding="utf-8")
        print(f"\n[INFO] Saved → {p}")


if __name__ == "__main__":
    main()
