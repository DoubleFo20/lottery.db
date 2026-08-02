"""
Lottery Data Scraper
====================
Sources:
  - Primary:   https://www.thairath.co.th/lottery/archive
  - Secondary: https://www.myhora.com/lottery/stats.aspx?mx=09&vx=10

Output:
  database/dataset/lottery_history.csv

Columns:
  draw_date, first_prize,
  front3_1, front3_2, back3_1, back3_2, last2,
  digit1, digit2, digit3, digit4, digit5, digit6

Requirements:
  pip install requests beautifulsoup4 lxml
"""


import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import csv
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]  # project root
OUTPUT_CSV = BASE_DIR / "database" / "dataset" / "lottery_history.csv"

THAIRATH_BASE = "https://www.thairath.co.th/lottery/archive"
MYHORA_URL    = "https://www.myhora.com/lottery/stats.aspx?mx=09&vx=10"

# Thai Buddhist years to scrape (BE 2558 = CE 2015 … BE 2569 = CE 2026)
THAI_YEARS = list(range(2558, 2570))   # 2558 – 2569 inclusive

CSV_COLUMNS = [
    "draw_date",
    "first_prize",
    "front3_1", "front3_2",
    "back3_1",  "back3_2",
    "last2",
    "digit1", "digit2", "digit3", "digit4", "digit5", "digit6",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
}

REQUEST_DELAY = 1.0   # seconds between requests

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thai date parsing
# ---------------------------------------------------------------------------

THAI_MONTHS = {
    "มกราคม":   1, "กุมภาพันธ์": 2, "มีนาคม":    3,
    "เมษายน":   4, "พฤษภาคม":   5, "มิถุนายน":   6,
    "กรกฎาคม":  7, "สิงหาคม":   8, "กันยายน":    9,
    "ตุลาคม":  10, "พฤศจิกายน": 11, "ธันวาคม":   12,
}

# Correct Thai month names and result labels. Stored as escapes to avoid
# mojibake breaking scraper matches on Thai pages.
THAI_MONTHS = {
    "\u0e21\u0e01\u0e23\u0e32\u0e04\u0e21": 1,
    "\u0e01\u0e38\u0e21\u0e20\u0e32\u0e1e\u0e31\u0e19\u0e18\u0e4c": 2,
    "\u0e21\u0e35\u0e19\u0e32\u0e04\u0e21": 3,
    "\u0e40\u0e21\u0e29\u0e32\u0e22\u0e19": 4,
    "\u0e1e\u0e24\u0e29\u0e20\u0e32\u0e04\u0e21": 5,
    "\u0e21\u0e34\u0e16\u0e38\u0e19\u0e32\u0e22\u0e19": 6,
    "\u0e01\u0e23\u0e01\u0e0e\u0e32\u0e04\u0e21": 7,
    "\u0e2a\u0e34\u0e07\u0e2b\u0e32\u0e04\u0e21": 8,
    "\u0e01\u0e31\u0e19\u0e22\u0e32\u0e22\u0e19": 9,
    "\u0e15\u0e38\u0e25\u0e32\u0e04\u0e21": 10,
    "\u0e1e\u0e24\u0e28\u0e08\u0e34\u0e01\u0e32\u0e22\u0e19": 11,
    "\u0e18\u0e31\u0e19\u0e27\u0e32\u0e04\u0e21": 12,
}

LABEL_FIRST = "\u0e23\u0e32\u0e07\u0e27\u0e31\u0e25\u0e17\u0e35\u0e48 1"
LABEL_FRONT3 = ("\u0e40\u0e25\u0e02\u0e2b\u0e19\u0e49\u0e32 3 \u0e15\u0e31\u0e27", "\u0e2b\u0e19\u0e49\u0e32 3 \u0e15\u0e31\u0e27")
LABEL_BACK3 = ("\u0e40\u0e25\u0e02\u0e17\u0e49\u0e32\u0e22 3 \u0e15\u0e31\u0e27", "\u0e17\u0e49\u0e32\u0e22 3 \u0e15\u0e31\u0e27")
LABEL_LAST2 = ("\u0e40\u0e25\u0e02\u0e17\u0e49\u0e32\u0e22 2 \u0e15\u0e31\u0e27", "\u0e17\u0e49\u0e32\u0e22 2 \u0e15\u0e31\u0e27")


def contains_any(text: str, needles) -> bool:
    if isinstance(needles, str):
        needles = (needles,)
    return any(needle in text for needle in needles)


def parse_thai_date(text: str) -> str | None:
    """
    Parse a Thai date string like 'ตรวจหวย 16 ธันวาคม 2568'
    and return ISO 8601 string 'YYYY-MM-DD' (CE).
    Returns None on failure.
    """
    pattern = r"(\d{1,2})\s+([\u0E00-\u0E7F]+)\s+(\d{4})"
    m = re.search(pattern, text)
    if not m:
        return None
    day, month_th, be_year = int(m.group(1)), m.group(2), int(m.group(3))
    month = THAI_MONTHS.get(month_th)
    if month is None:
        return None
    ce_year = be_year - 543
    try:
        return datetime(ce_year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Digit splitter
# ---------------------------------------------------------------------------

def split_digits(number: str) -> dict:
    """Return digit1..digit6 from a 6-digit string."""
    n = number.zfill(6)[:6]
    return {f"digit{i+1}": n[i] for i in range(6)}


# ---------------------------------------------------------------------------
# Thairath scraper
# ---------------------------------------------------------------------------

def fetch(url: str) -> BeautifulSoup | None:
    """Fetch URL and return BeautifulSoup object, or None on error."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as exc:
        log.warning("Failed to fetch %s — %s", url, exc)
        return None


def scrape_thairath() -> list[dict]:
    """
    Scrape all draw results from Thairath archive pages.
    Returns a list of row dicts ready for CSV.
    """
    all_rows: list[dict] = []

    for be_year in THAI_YEARS:
        url = f"{THAIRATH_BASE}/{be_year}"
        log.info("Fetching Thairath year %d  →  %s", be_year, url)
        soup = fetch(url)
        if soup is None:
            continue

        rows = parse_thairath_page(soup, be_year)
        log.info("  Found %d draws", len(rows))
        all_rows.extend(rows)
        time.sleep(REQUEST_DELAY)

    return all_rows


def parse_thairath_page(soup: BeautifulSoup, be_year: int) -> list[dict]:
    """
    Parse a Thairath archive page for one Thai Buddhist year.

    Page structure (simplified):
        <h2>ตรวจหวย 16 ธันวาคม 2568 ...</h2>
        <h2>รางวัลที่ 1</h2>   ← followed by text node "763895"
        <h2>เลขหน้า 3 ตัว</h2>  ← followed by two 3-digit strings
        <h2>เลขท้าย 3 ตัว</h2>  ← followed by two 3-digit strings
        <h2>เลขท้าย 2 ตัว</h2>  ← followed by a 2-digit string
    """
    rows: list[dict] = []

    # Collect all h2 tags and their following sibling text nodes
    headings = soup.find_all("h2")

    # Build a flat list of (type, value) pairs ordered as they appear
    # We'll scan through headings looking for draw date patterns
    draw_blocks: list[dict] = []
    current: dict | None = None

    for h in headings:
        text = h.get_text(separator=" ", strip=True)

        # ── Draw date heading ──────────────────────────────────────────
        date_str = parse_thai_date(text)
        if date_str:
            if current:
                draw_blocks.append(current)
            current = {
                "draw_date": date_str,
                "first_prize": "",
                "front3": [],
                "back3": [],
                "last2": "",
            }
            continue

        if current is None:
            continue

        # ── Gather numbers from the next sibling nodes ─────────────────
        numbers = _collect_numbers_after(h)

        if "รางวัลที่ 1" in text:
            if numbers:
                current["first_prize"] = numbers[0]

        elif "เลขหน้า 3 ตัว" in text or "หน้า 3 ตัว" in text:
            current["front3"].extend(numbers[:2])

        elif "เลขท้าย 3 ตัว" in text or "ท้าย 3 ตัว" in text:
            current["back3"].extend(numbers[:2])

        elif "เลขท้าย 2 ตัว" in text or "ท้าย 2 ตัว" in text:
            if not current["last2"] and numbers:
                current["last2"] = numbers[0]

    # Don't forget the last block
    if current:
        draw_blocks.append(current)

    # ── Convert blocks → CSV rows ──────────────────────────────────────
    for block in draw_blocks:
        fp = block.get("first_prize", "")
        if not fp:
            log.debug("  Skip draw %s — no first prize found", block["draw_date"])
            continue

        front3 = block.get("front3", [])
        back3  = block.get("back3", [])

        row = {
            "draw_date":  block["draw_date"],
            "first_prize": fp,
            "front3_1": front3[0] if len(front3) > 0 else "",
            "front3_2": front3[1] if len(front3) > 1 else "",
            "back3_1":  back3[0]  if len(back3)  > 0 else "",
            "back3_2":  back3[1]  if len(back3)  > 1 else "",
            "last2":    block.get("last2", ""),
        }
        row.update(split_digits(fp))
        rows.append(row)

    return rows


def _collect_numbers_after(tag) -> list[str]:
    """
    Walk subsequent siblings of a heading tag and collect digit tokens
    (strings of 2-6 decimal characters) until the next heading.
    """
    numbers: list[str] = []
    for sib in tag.next_siblings:
        if sib.name and sib.name in ("h1", "h2", "h3"):
            break
        raw = sib.get_text(separator="\n", strip=True) if hasattr(sib, "get_text") else str(sib).strip()
        for token in re.split(r"\s+", raw):
            if re.fullmatch(r"\d{2,6}", token):
                numbers.append(token)
    return numbers


# ---------------------------------------------------------------------------
# myhora scraper (secondary / fallback)
# ---------------------------------------------------------------------------

def scrape_myhora() -> list[dict]:
    """
    Attempt to fetch myhora lottery stats page.
    Returns list of row dicts or empty list if blocked.
    """
    log.info("Fetching myhora  →  %s", MYHORA_URL)
    myhora_headers = {**HEADERS, "Referer": "https://www.myhora.com/"}
    try:
        resp = requests.get(MYHORA_URL, headers=myhora_headers, timeout=20)
        if resp.status_code == 403:
            log.warning("myhora returned 403 — skipping secondary source")
            return []
        resp.raise_for_status()
    except Exception as exc:
        log.warning("myhora fetch failed — %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    rows: list[dict] = []

    # myhora table rows: look for rows with lottery result data
    # The page typically has a table with columns for date and prize numbers
    for tr in soup.select("table tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if len(cells) < 4:
            continue

        # Try to find the date cell
        date_str = None
        for cell in cells:
            date_str = parse_thai_date(cell)
            if date_str:
                break
        if not date_str:
            continue

        # Extract digit sequences from remaining cells
        all_nums = []
        for cell in cells:
            for token in re.split(r"\s+", cell):
                if re.fullmatch(r"\d{2,6}", token):
                    all_nums.append(token)

        if not all_nums:
            continue

        # Best-effort mapping: first 6-digit number = first_prize
        fp = next((n for n in all_nums if len(n) == 6), "")
        if not fp:
            continue

        threes = [n for n in all_nums if len(n) == 3]
        twos   = [n for n in all_nums if len(n) == 2]

        row = {
            "draw_date":   date_str,
            "first_prize": fp,
            "front3_1": threes[0] if len(threes) > 0 else "",
            "front3_2": threes[1] if len(threes) > 1 else "",
            "back3_1":  threes[2] if len(threes) > 2 else "",
            "back3_2":  threes[3] if len(threes) > 3 else "",
            "last2":    twos[0]   if twos else "",
        }
        row.update(split_digits(fp))
        rows.append(row)

    log.info("myhora: found %d draws", len(rows))
    return rows


# ---------------------------------------------------------------------------
# Merge & deduplicate
# ---------------------------------------------------------------------------

def merge_results(primary: list[dict], secondary: list[dict]) -> list[dict]:
    """
    Merge primary and secondary results, de-duplicating by draw_date.
    Primary always wins on conflict.
    """
    seen: dict[str, dict] = {}
    for row in primary:
        seen[row["draw_date"]] = row
    for row in secondary:
        if row["draw_date"] not in seen:
            seen[row["draw_date"]] = row
    # Sort newest first
    return sorted(seen.values(), key=lambda r: r["draw_date"], reverse=True)


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------

def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    log.info("Saved %d rows to %s", len(rows), path)


# ---------------------------------------------------------------------------
# Encoding-safe Thairath parser override
# ---------------------------------------------------------------------------

def parse_thairath_page(soup: BeautifulSoup, be_year: int) -> list[dict]:
    rows: list[dict] = []
    draw_blocks: list[dict] = []
    current: dict | None = None

    for h in soup.find_all("h2"):
        text = h.get_text(separator=" ", strip=True)
        date_str = parse_thai_date(text)

        if date_str:
            if current:
                draw_blocks.append(current)
            current = {
                "draw_date": date_str,
                "first_prize": "",
                "front3": [],
                "back3": [],
                "last2": "",
            }
            continue

        if current is None:
            continue

        numbers = _collect_numbers_after(h)
        if contains_any(text, LABEL_FIRST) and numbers:
            current["first_prize"] = next((n for n in numbers if len(n) == 6), numbers[0])
        elif contains_any(text, LABEL_FRONT3):
            current["front3"].extend([n for n in numbers if len(n) == 3][:2])
        elif contains_any(text, LABEL_BACK3):
            current["back3"].extend([n for n in numbers if len(n) == 3][:2])
        elif contains_any(text, LABEL_LAST2):
            twos = [n for n in numbers if len(n) == 2]
            if not current["last2"] and twos:
                current["last2"] = twos[0]

    if current:
        draw_blocks.append(current)

    for block in draw_blocks:
        fp = block.get("first_prize", "")
        if not re.fullmatch(r"\d{6}", fp or ""):
            continue

        front3 = block.get("front3", [])
        back3 = block.get("back3", [])
        row = {
            "draw_date": block["draw_date"],
            "first_prize": fp,
            "front3_1": front3[0] if len(front3) > 0 else "",
            "front3_2": front3[1] if len(front3) > 1 else "",
            "back3_1": back3[0] if len(back3) > 0 else "",
            "back3_2": back3[1] if len(back3) > 1 else "",
            "last2": block.get("last2", ""),
        }
        row.update(split_digits(fp))
        rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("=== Lottery Scraper Started ===")

    primary   = scrape_thairath()
    secondary = scrape_myhora()

    merged = merge_results(primary, secondary)

    if not merged:
        log.error("No data collected — CSV not written.")
        return

    write_csv(merged, OUTPUT_CSV)
    log.info("=== Done: %d total draws ===", len(merged))

    # Quick preview
    print("\n--- Preview (first 3 rows) ---")
    for row in merged[:3]:
        print(row)


if __name__ == "__main__":
    main()
