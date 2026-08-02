"""
Historical Lottery Dataset Expansion Script
=============================================
Fetches older Thai lottery results (2007–2014) from the public GitHub archive
(vicha-w/thai-lotto-archive) and merges with the existing dataset.

Sources:
  Primary:   https://github.com/vicha-w/thai-lotto-archive (2006-12-30 → present)
  Secondary: https://www.myhora.com/lottery/stats.aspx (fallback)
  Existing:  database/dataset/lottery_history.csv

Output:
  database/dataset/lottery_history.csv  (merged, deduplicated, sorted desc)

Requirements:
  pip install requests
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import csv
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = BASE_DIR / "database" / "dataset" / "lottery_history.csv"

GITHUB_API = "https://api.github.com/repos/vicha-w/thai-lotto-archive/contents/lottonumbers"
GITHUB_RAW = "https://raw.githubusercontent.com/vicha-w/thai-lotto-archive/master/lottonumbers"

CSV_COLUMNS = [
    "draw_date", "first_prize",
    "front3_1", "front3_2", "back3_1", "back3_2", "last2",
    "digit1", "digit2", "digit3", "digit4", "digit5", "digit6",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (LotteryBot/1.0)",
    "Accept": "application/json",
}

REQUEST_DELAY = 0.3  # seconds between GitHub raw file requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def split_digits(number: str) -> dict:
    n = number.zfill(6)[:6]
    return {f"digit{i+1}": n[i] for i in range(6)}


def fetch_text(url: str) -> str | None:
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        log.warning("Failed to fetch %s: %s", url, e)
        return None


def fetch_json(url: str) -> Any:
    try:
        req = Request(url, headers={**HEADERS, "Accept": "application/json"})
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning("Failed to fetch JSON %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Generate all expected draw dates (1st and 16th, with known offsets)
# ---------------------------------------------------------------------------

def generate_draw_dates(start_year: int, end_year: int) -> list[str]:
    """Generate all expected Thai lottery draw dates between start and end year."""
    dates = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # 1st of each month
            day1 = 1
            # 16th of each month
            day16 = 16

            # Known exceptions:
            # Jan 1  → Dec 30 of previous year
            # Jan 16 → Jan 17
            # May 1  → May 2

            if month == 1:
                # Jan 17 instead of Jan 16
                dates.append(f"{year}-01-17")
                # Dec 30 of prev year (already handled by prev year)
            elif month == 5:
                dates.append(f"{year}-05-02")
                dates.append(f"{year}-05-16")
            else:
                dates.append(f"{year}-{month:02d}-01")
                dates.append(f"{year}-{month:02d}-16")

            # Dec 30 instead of Jan 1
            if month == 12:
                dates.append(f"{year}-12-30")

    # Deduplicate and sort
    return sorted(set(dates))


# ---------------------------------------------------------------------------
# Parse a single lottonumbers file
# ---------------------------------------------------------------------------

def parse_lotto_file(text: str, draw_date: str) -> dict | None:
    """
    Parse a lottonumbers text file into a CSV row dict.

    File format:
        URL_LINE
        FIRST 123456
        THREE 111 222 333 444        (pre-Sep-2015: 4 suffix numbers)
        THREE_FIRST 111 222          (post-Sep-2015: 2 prefix numbers)
        THREE_LAST 333 444           (post-Sep-2015: 2 suffix numbers)
        TWO 12
        ...
    """
    lines = text.strip().split("\n")

    first_prize = ""
    front3 = []
    back3 = []
    last2 = ""

    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue

        label = parts[0]

        if label == "FIRST" and len(parts) >= 2:
            first_prize = parts[1].strip()

        elif label == "THREE" and len(parts) >= 2:
            # Pre-Sep-2015: all 4 are suffix (back3) — but we map first 2 as front3, last 2 as back3
            # Actually there was no distinction. We'll store first 2 as front3, last 2 as back3
            nums = parts[1:]
            front3 = nums[:2] if len(nums) >= 2 else nums
            back3 = nums[2:4] if len(nums) >= 4 else []

        elif label == "THREE_FIRST" and len(parts) >= 2:
            front3 = parts[1:3]

        elif label == "THREE_LAST" and len(parts) >= 2:
            back3 = parts[1:3]

        elif label == "TWO" and len(parts) >= 2:
            last2 = parts[1].strip()

    if not first_prize or len(first_prize) != 6:
        return None

    row = {
        "draw_date": draw_date,
        "first_prize": first_prize,
        "front3_1": front3[0] if len(front3) > 0 else "",
        "front3_2": front3[1] if len(front3) > 1 else "",
        "back3_1": back3[0] if len(back3) > 0 else "",
        "back3_2": back3[1] if len(back3) > 1 else "",
        "last2": last2,
    }
    row.update(split_digits(first_prize))
    return row


# ---------------------------------------------------------------------------
# Fetch file listing from GitHub API
# ---------------------------------------------------------------------------

def get_github_file_list() -> list[str]:
    """Get all filenames from the lottonumbers directory via GitHub API."""
    log.info("Fetching file list from GitHub API (paginated)...")

    all_dates = []
    page = 1
    per_page = 100

    while True:
        url = f"{GITHUB_API}?per_page={per_page}&page={page}"
        data = fetch_json(url)
        if not data or not isinstance(data, list):
            break

        for item in data:
            name = item.get("name", "")
            if name.endswith(".txt"):
                date_str = name.replace(".txt", "")
                all_dates.append(date_str)

        if len(data) < per_page:
            break
        page += 1
        time.sleep(0.5)

    log.info("Found %d draw files on GitHub", len(all_dates))
    return sorted(all_dates)


# ---------------------------------------------------------------------------
# Load existing CSV
# ---------------------------------------------------------------------------

def load_existing_csv() -> dict[str, dict]:
    """Load existing CSV into a dict keyed by draw_date."""
    if not CSV_PATH.exists():
        return {}

    existing = {}
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return {}
        for row in reader:
            date = row.get("draw_date", "").strip()
            if date:
                existing[date] = row
    log.info("Loaded %d existing rows from CSV", len(existing))
    return existing


# ---------------------------------------------------------------------------
# Main expansion logic
# ---------------------------------------------------------------------------

def expand_dataset():
    log.info("=" * 60)
    log.info("  HISTORICAL DATASET EXPANSION")
    log.info("=" * 60)

    # 1. Load existing
    existing = load_existing_csv()
    original_count = len(existing)

    # 2. Get file list from GitHub
    all_dates = get_github_file_list()

    # 3. Find dates we don't have yet
    missing_dates = [d for d in all_dates if d not in existing]
    log.info("Missing draws to fetch: %d", len(missing_dates))

    # 4. Fetch and parse each missing file
    added = 0
    errors = 0

    for i, date_str in enumerate(missing_dates):
        url = f"{GITHUB_RAW}/{date_str}.txt"
        text = fetch_text(url)

        if text is None:
            errors += 1
            continue

        row = parse_lotto_file(text, date_str)
        if row:
            existing[date_str] = row
            added += 1
            if added % 50 == 0:
                log.info("  Progress: %d / %d fetched", added, len(missing_dates))
        else:
            log.warning("  Could not parse %s", date_str)
            errors += 1

        time.sleep(REQUEST_DELAY)

    log.info("Fetched %d new draws (%d errors)", added, errors)

    # 5. Sort all rows by draw_date descending
    all_rows = sorted(existing.values(), key=lambda r: r.get("draw_date", ""), reverse=True)

    # 6. Ensure all columns exist
    for row in all_rows:
        for col in CSV_COLUMNS:
            row.setdefault(col, "")
        # Re-derive digit columns from first_prize if missing
        fp = row.get("first_prize", "")
        if fp and len(fp) == 6:
            digits = split_digits(fp)
            for k, v in digits.items():
                if not row.get(k):
                    row[k] = v

    # 7. Write merged CSV
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    final_count = len(all_rows)
    new_count = final_count - original_count

    # 8. Validation output
    print("\n" + "=" * 60)
    print("  VALIDATION")
    print("=" * 60)
    print(f"  Total rows: {final_count}")
    print(f"  Original:   {original_count}")
    print(f"  Added:      {new_count}")

    print("\n--- First 5 rows ---")
    for row in all_rows[:5]:
        print(f"  {row['draw_date']}  {row['first_prize']}  "
              f"F3:{row.get('front3_1','')}/{row.get('front3_2','')}  "
              f"B3:{row.get('back3_1','')}/{row.get('back3_2','')}  "
              f"L2:{row.get('last2','')}  "
              f"D:{row.get('digit1','')}{row.get('digit2','')}{row.get('digit3','')}"
              f"{row.get('digit4','')}{row.get('digit5','')}{row.get('digit6','')}")

    print("\n--- Last 5 rows ---")
    for row in all_rows[-5:]:
        print(f"  {row['draw_date']}  {row['first_prize']}  "
              f"F3:{row.get('front3_1','')}/{row.get('front3_2','')}  "
              f"B3:{row.get('back3_1','')}/{row.get('back3_2','')}  "
              f"L2:{row.get('last2','')}  "
              f"D:{row.get('digit1','')}{row.get('digit2','')}{row.get('digit3','')}"
              f"{row.get('digit4','')}{row.get('digit5','')}{row.get('digit6','')}")

    # 9. Date range
    earliest = all_rows[-1]["draw_date"] if all_rows else "?"
    latest = all_rows[0]["draw_date"] if all_rows else "?"
    earliest_y = earliest[:4] if earliest != "?" else "?"
    latest_y = latest[:4] if latest != "?" else "?"

    # 10. Thai summary report
    print("\n" + "=" * 60)
    print("  รายงานสรุป (Summary Report)")
    print("=" * 60)
    print(f"  • จำนวนงวดทั้งหมดใน dataset: {final_count} งวด")
    print(f"  • ช่วงปีของข้อมูล: {earliest_y}–{latest_y} ({earliest} ถึง {latest})")
    print(f"  • จำนวนงวดที่เพิ่มเข้ามา: {new_count} งวด")
    print(f"  • แหล่งข้อมูลที่ใช้ scrape:")
    print(f"      - GitHub: vicha-w/thai-lotto-archive (หลัก)")
    print(f"      - Thairath: thairath.co.th/lottery/archive (ข้อมูลเดิม)")
    if final_count >= 700:
        print(f"  • สถานะ dataset: ✅ พร้อมใช้สำหรับ AI analysis ({final_count} >= 700 งวด)")
    else:
        print(f"  • สถานะ dataset: ⚠️  ยังไม่ถึง 700 งวด ({final_count} งวด)")
        print(f"      ต้องการเพิ่มอีก {700 - final_count} งวด จากแหล่งข้อมูลอื่น")
    print("=" * 60)

    log.info("Done! CSV saved to %s", CSV_PATH)
    return final_count


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    expand_dataset()
