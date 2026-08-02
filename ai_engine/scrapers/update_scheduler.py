"""
Automatic Dataset Updater & Scheduler
======================================
Checks daily for new Thai lottery draws, scrapes the latest result from
Thairath, appends to the CSV dataset, and inserts into MySQL database.

Triggers:
  - Lottery draw days: 1st and 16th of every month (with standard exceptions)
  - Runs a check loop every 24 hours via schedule

Database:
  MySQL → lottery_ai.lottery_results  (localhost / root / "")

Requirements:
  pip install requests beautifulsoup4 lxml schedule mysql-connector-python

Run:
  python ai_engine/scrapers/update_scheduler.py          # daemon mode
  python ai_engine/scrapers/update_scheduler.py --now    # force immediate check
  python ai_engine/scrapers/update_scheduler.py --date 2026-03-16  # specific date
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import csv
import logging
import os
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR    = Path(__file__).resolve().parents[2]
CSV_PATH    = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
LOG_PATH    = BASE_DIR / "ai_engine" / "scrapers" / "updater.log"

CSV_COLUMNS = [
    "draw_date", "first_prize",
    "front3_1", "front3_2", "back3_1", "back3_2", "last2",
    "digit1", "digit2", "digit3", "digit4", "digit5", "digit6",
]

THAIRATH_BASE = "https://www.thairath.co.th/lottery/archive"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8",
}

# MySQL connection settings — mirror of backend/config/database.php
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",
    "database": "lottery_ai",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Draw-date logic
# ---------------------------------------------------------------------------

def is_draw_day(d: date) -> bool:
    """Return True if `d` is an official Thai lottery draw day."""
    # Standard: 1st and 16th
    # Exception: Jan 16 → Jan 17 | May 1 → May 2 | Jan 1 → Dec 30 prev year
    # Dec 30 is a draw day instead of Jan 1 (handled in get_draw_dates_for_month)
    if d.day == 1:
        if d.month == 1:   # New Year - no draw on Jan 1
            return False
        if d.month == 5:   # Labour Day - draw is May 2 instead
            return False
        return True
    if d.day == 2 and d.month == 5:    # Labour Day replacement
        return True
    if d.day == 16:
        if d.month == 1:   # Teacher's Day - draw is Jan 17 instead
            return False
        return True
    if d.day == 17 and d.month == 1:   # Teacher's Day replacement
        return True
    if d.day == 30 and d.month == 12:  # Dec 30 replaces Jan 1 of next year
        return True
    return False


def next_draw_date(from_date: date | None = None) -> date:
    """Return the next draw date on or after from_date."""
    if from_date is None:
        from_date = date.today()

    d = from_date
    for _ in range(60):   # scan at most 60 days forward
        if is_draw_day(d):
            return d
        d += timedelta(days=1)
    raise RuntimeError("Could not find next draw date within 60 days")


def latest_draw_date_before_today() -> date | None:
    """Return the most recent draw date that has already passed (≤ today)."""
    today = date.today()
    # Scan backwards up to 20 days
    for i in range(20):
        d = today - timedelta(days=i)
        if is_draw_day(d):
            return d
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def split_digits(number: str) -> dict:
    n = number.zfill(6)[:6]
    return {f"digit{i+1}": n[i] for i in range(6)}


def load_existing_dates() -> set[str]:
    """Load all draw_dates already in the CSV."""
    if not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0:
        return set()
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return set()
        return {row["draw_date"].strip() for row in reader if row.get("draw_date")}


# ---------------------------------------------------------------------------
# Scraper (Thairath archive)
# ---------------------------------------------------------------------------

THAI_MONTHS = {
    "มกราคม":   1, "กุมภาพันธ์": 2, "มีนาคม":    3,
    "เมษายน":   4, "พฤษภาคม":   5, "มิถุนายน":   6,
    "กรกฎาคม":  7, "สิงหาคม":   8, "กันยายน":    9,
    "ตุลาคม":  10, "พฤศจิกายน": 11, "ธันวาคม":   12,
}


def _parse_thai_date(text: str) -> str | None:
    m = re.search(r"(\d{1,2})\s+([\u0E00-\u0E7F]+)\s+(\d{4})", text)
    if not m:
        return None
    day, month_th, be_year = int(m.group(1)), m.group(2), int(m.group(3))
    month = THAI_MONTHS.get(month_th)
    if not month:
        return None
    ce_year = be_year - 543
    try:
        return datetime(ce_year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _collect_numbers_after(tag) -> list[str]:
    nums = []
    for sib in tag.next_siblings:
        if sib.name and sib.name in ("h1", "h2", "h3"):
            break
        raw = sib.get_text(separator="\n", strip=True) if hasattr(sib, "get_text") else str(sib).strip()
        for tok in re.split(r"\s+", raw):
            if re.fullmatch(r"\d{2,6}", tok):
                nums.append(tok)
    return nums


def scrape_draw(target_date: date) -> dict | None:
    """
    Scrape a single draw result for `target_date` from Thairath archive.
    Uses the Thai Buddhist year archive page and extracts the matching block.
    Returns a normalised CSV row dict, or None if not found.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        log.error("Missing dependencies. Run: pip install requests beautifulsoup4 lxml")
        return None

    # Thai Buddhist year
    be_year = target_date.year + 543
    url = f"{THAIRATH_BASE}/{be_year}"
    log.info("Scraping %s from %s", target_date.isoformat(), url)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        log.error("HTTP error fetching %s: %s", url, exc)
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    try:
        from ai_engine.scrapers.lottery_scraper import parse_thairath_page

        rows = parse_thairath_page(soup, be_year)
        target_str = target_date.strftime("%Y-%m-%d")
        for row in rows:
            if row.get("draw_date") == target_str:
                return row
    except Exception as exc:
        log.warning("Shared Thairath parser failed, falling back to local parser: %s", exc)

    headings = soup.find_all("h2")

    current: dict | None = None
    target_str = target_date.strftime("%Y-%m-%d")

    for h in headings:
        text = h.get_text(separator=" ", strip=True)
        date_str = _parse_thai_date(text)

        if date_str:
            if date_str == target_str:
                current = {
                    "draw_date": date_str,
                    "first_prize": "",
                    "front3": [],
                    "back3": [],
                    "last2": "",
                }
            elif current:
                # We've moved to the next draw block
                break
            continue

        if current is None:
            continue

        nums = _collect_numbers_after(h)

        if "รางวัลที่ 1" in text and nums:
            current["first_prize"] = nums[0]
        elif ("เลขหน้า 3 ตัว" in text or "หน้า 3 ตัว" in text):
            current["front3"].extend(nums[:2])
        elif ("เลขท้าย 3 ตัว" in text or "ท้าย 3 ตัว" in text):
            current["back3"].extend(nums[:2])
        elif ("เลขท้าย 2 ตัว" in text or "ท้าย 2 ตัว" in text):
            if not current["last2"] and nums:
                current["last2"] = nums[0]

    if not current or not current.get("first_prize"):
        log.warning("No result found for %s", target_str)
        return None

    fp = current["first_prize"]
    front3 = current.get("front3", [])
    back3  = current.get("back3", [])

    row = {
        "draw_date":   target_str,
        "first_prize": fp,
        "front3_1": front3[0] if len(front3) > 0 else "",
        "front3_2": front3[1] if len(front3) > 1 else "",
        "back3_1":  back3[0]  if len(back3)  > 0 else "",
        "back3_2":  back3[1]  if len(back3)  > 1 else "",
        "last2":    current.get("last2", ""),
    }
    row.update(split_digits(fp))
    return row


# ---------------------------------------------------------------------------
# CSV append
# ---------------------------------------------------------------------------

def append_to_csv(row: dict) -> None:
    """Append one row to the CSV dataset, sorted by draw_date descending."""
    # Load all existing rows
    existing: dict[str, dict] = {}
    if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                for r in reader:
                    existing[r["draw_date"].strip()] = r

    # Merge new row (overwrite if date already exists)
    existing[row["draw_date"]] = row

    # Re-sort descending
    all_rows = sorted(existing.values(), key=lambda r: r["draw_date"], reverse=True)

    # Write back
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    log.info("CSV updated - %d total rows", len(all_rows))


# ---------------------------------------------------------------------------
# MySQL insert
# ---------------------------------------------------------------------------

def insert_to_db(row: dict) -> bool:
    """Insert (or ignore duplicate) a draw result into MySQL lottery_results."""
    try:
        import mysql.connector
    except ImportError:
        log.warning("mysql-connector-python not installed - skipping DB insert")
        return False

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        sql = """
            INSERT IGNORE INTO lottery_results
                (draw_date, first_prize, last2, digit1, digit2, digit3, digit4, digit5, digit6)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            row["draw_date"],
            row["first_prize"],
            row.get("last2", ""),
            int(row.get("digit1", 0)),
            int(row.get("digit2", 0)),
            int(row.get("digit3", 0)),
            int(row.get("digit4", 0)),
            int(row.get("digit5", 0)),
            int(row.get("digit6", 0)),
        )
        cursor.execute(sql, values)
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()

        if affected > 0:
            log.info("DB insert OK - draw_date=%s  first_prize=%s",
                     row["draw_date"], row["first_prize"])
        else:
            log.info("DB: draw_date=%s already exists (INSERT IGNORE)", row["draw_date"])
        return True

    except Exception as exc:
        log.error("DB insert failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Trigger downstream pipelines
# ---------------------------------------------------------------------------

def trigger_feature_pipelines() -> None:
    """Re-run feature_engineering and temporal_weight_engine after new data."""
    pipelines = [
        BASE_DIR / "analytics" / "feature_engineering.py",
        BASE_DIR / "analytics" / "temporal_weight_engine.py",
    ]
    for script in pipelines:
        if script.exists():
            log.info("Triggering pipeline: %s", script.name)
            exit_code = os.system(f'python "{script}"')
            if exit_code != 0:
                log.warning("Pipeline %s exited with code %d", script.name, exit_code)
        else:
            log.debug("Pipeline not found, skipping: %s", script)


# ---------------------------------------------------------------------------
# Core update job
# ---------------------------------------------------------------------------

def check_and_update(target_date: date | None = None) -> bool:
    """
    Main job: check if there's a new draw, scrape it, append CSV, insert DB.
    Returns True if a new result was inserted.
    """
    if target_date is None:
        target_date = latest_draw_date_before_today()

    if target_date is None:
        log.info("No draw day identified for today (%s)", date.today().isoformat())
        return False

    log.info("Checking draw date: %s", target_date.isoformat())

    existing_dates = load_existing_dates()
    if target_date.isoformat() in existing_dates:
        log.info("Draw %s already in dataset - no update needed", target_date.isoformat())
        return False

    # Scrape
    row = scrape_draw(target_date)
    if row is None:
        log.warning("Could not scrape result for %s - will retry next run", target_date.isoformat())
        return False

    log.info("Scraped: %s  first_prize=%s  last2=%s",
             row["draw_date"], row["first_prize"], row.get("last2", ""))

    # Persist
    append_to_csv(row)
    insert_to_db(row)

    # Update derived feature datasets
    trigger_feature_pipelines()

    log.info("[OK] Dataset updated with draw %s", target_date.isoformat())
    return True


# ---------------------------------------------------------------------------
# Scheduler daemon
# ---------------------------------------------------------------------------

def run_scheduler() -> None:
    """
    Run as a long-lived daemon that checks for new draws every 24 hours.
    Uses the standard `schedule` library if available, otherwise a simple
    sleep loop.
    """
    log.info("=" * 60)
    log.info("  Lottery Auto-Updater Scheduler started")
    log.info("  Check times: 15:45, 16:15, 17:00, 21:00 TH")
    log.info("=" * 60)

    # Do an immediate check on startup
    check_and_update()

    try:
        import schedule

        schedule.every().day.at("15:45").do(check_and_update)
        schedule.every().day.at("16:15").do(check_and_update)
        schedule.every().day.at("17:00").do(check_and_update)
        schedule.every().day.at("21:00").do(check_and_update)

        log.info("Scheduler active - waiting for next draw day...")
        while True:
            schedule.run_pending()
            time.sleep(60)   # poll every minute

    except ImportError:
        # Fallback: simple 24-hour sleep loop
        log.warning("'schedule' package not installed - using 24-hour sleep loop")
        log.warning("Install with: pip install schedule")
        while True:
            log.info("Next check in 24 hours")
            time.sleep(86400)
            check_and_update()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Thai Lottery Automatic Dataset Updater"
    )
    parser.add_argument(
        "--now", action="store_true",
        help="Force an immediate check and update, then exit"
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="Check a specific draw date (YYYY-MM-DD), then exit"
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Run as a continuous scheduler daemon (default behaviour)"
    )
    args = parser.parse_args()

    if args.date:
        try:
            target = date.fromisoformat(args.date)
        except ValueError:
            log.error("Invalid date format '%s'. Use YYYY-MM-DD.", args.date)
            sys.exit(1)
        result = check_and_update(target_date=target)
        sys.exit(0 if result else 1)

    if args.now:
        result = check_and_update()
        sys.exit(0 if result else 1)

    # Default: daemon mode
    run_scheduler()


if __name__ == "__main__":
    main()
