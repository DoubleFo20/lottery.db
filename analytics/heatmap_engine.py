"""
Digit Heatmap Engine
======================
Generates heatmap matrices from Thai lottery digit history.

Input:  database/dataset/lottery_history.csv
Cols:   digit1 … digit6

Matrices produced:
  1. Position × Digit  — P(digit | position)  [6 × 10]
  2. Digit × Digit     — co-occurrence across all position pairs  [10 × 10]
  3. Per-draw rolling heat  — average frequency in sliding window
  4. Temporal heatmap       — decade / 5-year hot/cold map

Output: printed ASCII heatmap + optional JSON export

Usage:
  python analytics/heatmap_engine.py
  python analytics/heatmap_engine.py --json
  python analytics/heatmap_engine.py --save heatmap_output.json
  python analytics/heatmap_engine.py --window 50
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path

# ---------------------------------------------------------------------------
BASE_DIR    = Path(__file__).resolve().parents[1]
DEFAULT_CSV = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
DIGIT_COLS  = ["digit1", "digit2", "digit3", "digit4", "digit5", "digit6"]
ALL_DIGITS  = [str(d) for d in range(10)]

# ASCII shade blocks — lightest to darkest
SHADES = [" ", "░", "▒", "▓", "█"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load(path: Path) -> list[dict]:
    if not path.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if all(row.get(c, "").isdigit() for c in DIGIT_COLS):
                rows.append(row)
    print(f"[INFO] Loaded {len(rows)} valid draws")
    return rows


# ---------------------------------------------------------------------------
# Matrix builders
# ---------------------------------------------------------------------------

def build_position_digit_matrix(rows: list[dict]) -> dict:
    """
    Matrix [6 × 10]: P(digit | position)
    Row = position (digit1-digit6), Col = digit (0-9)
    """
    n = len(rows)
    mat = {}
    for col in DIGIT_COLS:
        counts = {d: 0 for d in ALL_DIGITS}
        for row in rows:
            counts[row[col]] += 1
        total = sum(counts.values())
        mat[col] = {d: round(counts[d] / total, 5) for d in ALL_DIGITS}
    return mat


def build_cooccurrence_matrix(rows: list[dict]) -> dict:
    """
    Matrix [10 × 10]: normalised co-occurrence count of digit pairs
    across all C(6,2) position combinations.
    """
    count = defaultdict(int)
    total = 0
    for row in rows:
        vals = [row[c] for c in DIGIT_COLS]
        for i, j in combinations(range(6), 2):
            a, b = vals[i], vals[j]
            count[(a, b)] += 1
            count[(b, a)] += 1
            total += 2

    mat = {}
    for a in ALL_DIGITS:
        mat[a] = {}
        for b in ALL_DIGITS:
            mat[a][b] = round(count[(a, b)] / total, 6) if total else 0
    return mat


def build_rolling_heat(rows: list[dict], window: int = 50) -> dict:
    """
    Rolling frequency for each digit over the last `window` draws.
    Returns {digit: frequency_in_window}
    """
    recent = rows[:window]
    counts = {d: 0 for d in ALL_DIGITS}
    total = 0
    for row in recent:
        for col in DIGIT_COLS:
            counts[row[col]] += 1
            total += 1
    return {d: round(counts[d] / total, 5) for d in ALL_DIGITS}


def build_temporal_heatmap(rows: list[dict], band_years: int = 5) -> dict:
    """
    Groups draws into multi-year bands and computes digit frequency per band.
    Returns {band_label: {digit: freq}}
    """
    bands: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        try:
            year = int(row.get("draw_date", "2000")[:4])
            band_start = (year // band_years) * band_years
            label = f"{band_start}–{band_start + band_years - 1}"
            bands[label].append(row)
        except ValueError:
            pass

    result = {}
    for label in sorted(bands):
        band_rows = bands[label]
        counts = {d: 0 for d in ALL_DIGITS}
        total = 0
        for row in band_rows:
            for col in DIGIT_COLS:
                counts[row[col]] += 1
                total += 1
        result[label] = {
            "draws": len(band_rows),
            "freq": {d: round(counts[d] / total, 5) for d in ALL_DIGITS},
        }
    return result


# ---------------------------------------------------------------------------
# ASCII visualisation helpers
# ---------------------------------------------------------------------------

def _shade(value: float, lo: float, hi: float) -> str:
    if hi == lo:
        return SHADES[2]
    ratio = (value - lo) / (hi - lo)
    idx = min(int(ratio * len(SHADES)), len(SHADES) - 1)
    return SHADES[idx]


def print_position_digit_heatmap(mat: dict) -> None:
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│  POSITION × DIGIT HEATMAP  P(digit | position)                   │")
    print("│  Shade: ░=low  ▒=mid  ▓=high  █=peak                             │")
    print("├──────────┬" + "───────┬" * 9 + "───────┤")
    print("│ position │ " + " │ ".join(f"  {d}  " for d in ALL_DIGITS) + " │")
    print("├──────────┼" + "───────┼" * 9 + "───────┤")

    all_vals = [v for row in mat.values() for v in row.values()]
    lo, hi = min(all_vals), max(all_vals)

    for col, row in mat.items():
        cells = []
        for d in ALL_DIGITS:
            v = row[d]
            s = _shade(v, lo, hi)
            cells.append(f" {s}{v*100:4.1f}%")
        print(f"│ {col:<8} │" + " │".join(cells) + " │")

    print("└──────────┴" + "───────┴" * 9 + "───────┘")


def print_cooccurrence_heatmap(mat: dict) -> None:
    print("\n┌─────────────────────────────────────────┐")
    print("│  DIGIT × DIGIT CO-OCCURRENCE HEATMAP     │")
    print("│  (across all position pairs)              │")
    print("└─────────────────────────────────────────┘")
    print("     " + "  ".join(f" {d}" for d in ALL_DIGITS))
    print("   ┌" + "───" * 10 + "┐")

    all_vals = [mat[a][b] for a in ALL_DIGITS for b in ALL_DIGITS]
    lo, hi = min(all_vals), max(all_vals)

    for a in ALL_DIGITS:
        cells = []
        for b in ALL_DIGITS:
            v = mat[a][b]
            s = _shade(v, lo, hi)
            cells.append(f"{s}{s}")
        print(f" {a} │ " + " ".join(cells) + " │")
    print("   └" + "───" * 10 + "┘")


def print_rolling_heat(heat: dict, window: int) -> None:
    print(f"\n─── ROLLING HEAT (last {window} draws) ────────────────────────────")
    all_vals = list(heat.values())
    lo, hi = min(all_vals), max(all_vals)
    expected = 1 / 10

    for d in ALL_DIGITS:
        v = heat[d]
        bar_len = int(v / hi * 30)
        bar = "█" * bar_len
        diff = v - expected
        tag = "↑ HOT " if diff > 0.005 else ("↓ COLD" if diff < -0.005 else "  OK  ")
        print(f"  digit {d}: {bar:<30}  {v*100:5.2f}%  {tag}")


def print_temporal_heatmap(tmap: dict) -> None:
    print("\n─── TEMPORAL HEATMAP (5-year bands) ─────────────────────────────")
    all_vals = [v for band in tmap.values() for v in band["freq"].values()]
    lo, hi = min(all_vals), max(all_vals)

    header = "  Band        draws │ " + "  ".join(ALL_DIGITS)
    print(header)
    print("  " + "─" * (len(header) - 2))

    for label, data in sorted(tmap.items()):
        cells = []
        for d in ALL_DIGITS:
            v = data["freq"][d]
            s = _shade(v, lo, hi)
            cells.append(s * 2)
        print(f"  {label:<12}  {data['draws']:>4} │  " + "  ".join(cells))


# ---------------------------------------------------------------------------
# Master engine
# ---------------------------------------------------------------------------

class HeatmapEngine:

    def __init__(self, csv_path: str | Path = DEFAULT_CSV, window: int = 50):
        self.csv_path = Path(csv_path)
        self.window = window
        self.rows: list[dict] = []
        self.matrices: dict = {}

    def load(self) -> "HeatmapEngine":
        self.rows = load(self.csv_path)
        return self

    def build_all(self) -> "HeatmapEngine":
        if not self.rows:
            return self
        self.matrices = {
            "position_digit":  build_position_digit_matrix(self.rows),
            "cooccurrence":    build_cooccurrence_matrix(self.rows),
            "rolling_heat":    build_rolling_heat(self.rows, self.window),
            "temporal":        build_temporal_heatmap(self.rows),
            "meta": {
                "total_draws":  len(self.rows),
                "window":       self.window,
                "analyzed_at":  datetime.now().isoformat(),
                "source":       str(self.csv_path),
            },
        }
        return self

    def print_all(self) -> None:
        if not self.matrices:
            print("[ERROR] No matrices built yet — call build_all() first")
            return
        m = self.matrices
        print("\n" + "=" * 66)
        print("  LOTTERY DIGIT HEATMAP ENGINE")
        print(f"  Draws: {m['meta']['total_draws']}   Window: {m['meta']['window']}")
        print("=" * 66)
        print_position_digit_heatmap(m["position_digit"])
        print_cooccurrence_heatmap(m["cooccurrence"])
        print_rolling_heat(m["rolling_heat"], self.window)
        print_temporal_heatmap(m["temporal"])
        print("\n" + "=" * 66)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.matrices, ensure_ascii=False, indent=indent, default=str)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Lottery Digit Heatmap Engine")
    parser.add_argument("--csv",    type=str, default=str(DEFAULT_CSV))
    parser.add_argument("--window", type=int, default=50, help="Rolling window size")
    parser.add_argument("--json",   action="store_true", help="Print full JSON output")
    parser.add_argument("--save",   type=str, default="", help="Save JSON to file")
    args = parser.parse_args()

    engine = HeatmapEngine(args.csv, args.window)
    engine.load().build_all()

    if args.json:
        print(engine.to_json())
    else:
        engine.print_all()

    if args.save:
        p = Path(args.save)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(engine.to_json(), encoding="utf-8")
        print(f"\n[INFO] Saved → {p}")


if __name__ == "__main__":
    main()
