"""analytics/result_fetcher.py — Auto-fetch Thai Lottery Results & Trigger Pipeline"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[ERROR] Missing modules. Run: pip install requests beautifulsoup4")
    raise

BASE = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE))

try:
    from ai_engine.scrapers.lottery_scraper import fetch as fetch_html, parse_thairath_page, parse_thai_date
except ImportError:
    print("[ERROR] Could not import ai_engine.scrapers.lottery_scraper")
    raise

HISTORY_JSON = BASE / "database" / "predictions" / "prediction_history.json"
CSV_PATH     = BASE / "database" / "dataset" / "lottery_history.csv"
PERF_JSON    = BASE / "performance.json"

ICT = timezone(timedelta(hours=7))

THAI_MONTH_MAP = {
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4,
    "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8,
    "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12,
    "ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "เม.ย.": 4,
    "พ.ค.": 5, "มิ.ย.": 6, "ก.ค.": 7, "ส.ค.": 8,
    "ก.ย.": 9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12,
    "ม.ค": 1, "ก.พ": 2, "มี.ค": 3, "เม.ย": 4,
    "พ.ค": 5, "มิ.ย": 6, "ก.ค": 7, "ส.ค": 8,
    "ก.ย": 9, "ต.ค": 10, "พ.ย": 11, "ธ.ค": 12,
}


def set_github_output(name: str, value: str) -> None:
    output_file = os.getenv("GITHUB_OUTPUT")
    if output_file:
        try:
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"{name}={value}\n")
        except Exception as e:
            print(f"[WARN] Failed to write to GITHUB_OUTPUT: {e}")


def parse_thai_date_str(text: str) -> str | None:
    """Parse Thai date string into ISO 'YYYY-MM-DD'."""
    if not text:
        return None
    try:
        parsed = parse_thai_date(text)
        if parsed:
            # Sanity check: parse_thai_date always subtracts 543 (assumes BE).
            # If input was already CE (e.g. 2026), result year will be ~1483.
            # Reject implausible years and fall through to local regex.
            parsed_year = int(parsed.split("-")[0])
            if parsed_year >= 1900:
                return parsed
    except Exception:
        pass

    pattern = r"(\d{1,2})\s+([\u0E00-\u0E7F\.]+)\s+(\d{4})"
    m = re.search(pattern, text)
    if not m:
        return None
    day_str, month_str, year_str = m.group(1), m.group(2).strip(), m.group(3)
    try:
        day = int(day_str)
        month = THAI_MONTH_MAP.get(month_str) or THAI_MONTH_MAP.get(month_str.rstrip("."))
        if not month:
            return None
        be_year = int(year_str)
        ce_year = be_year - 543 if be_year > 2400 else be_year
        return datetime(ce_year, month, day).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def is_draw_day(d: date) -> bool:
    """Return True if d is an official Thai lottery draw day."""
    if d.day == 1:
        if d.month in (1, 5):
            return False
        return True
    if d.day == 2 and d.month == 5:
        return True
    if d.day == 16:
        if d.month == 1:
            return False
        return True
    if d.day == 17 and d.month == 1:
        return True
    if d.day == 30 and d.month == 12:
        return True
    return False


def get_expected_draw_date(reference_date: date | None = None) -> str:
    """
    Determine the expected Thai lottery draw date (YYYY-MM-DD).
    Default: Current date in Asia/Bangkok (UTC+7) timezone.
    If reference_date is an official draw day, returns reference_date.
    If not a draw day, returns the most recent passed draw date (<= reference_date).
    """
    if reference_date is None:
        ict_now = datetime.now(ICT)
        reference_date = ict_now.date()

    if is_draw_day(reference_date):
        return reference_date.strftime("%Y-%m-%d")

    for i in range(1, 35):
        d = reference_date - timedelta(days=i)
        if is_draw_day(d):
            return d.strftime("%Y-%m-%d")

    return reference_date.strftime("%Y-%m-%d")


def is_valid_draw_result(result: dict | None, target_date: str) -> bool:
    r"""
    Strict validation of fetched draw result:
    1. Result dictionary exists and is not empty.
    2. draw_date strictly matches target_date.
    3. first_prize is exactly 6 numeric digits (^\d{6}$).
    4. last2 is exactly 2 numeric digits (^\d{2}$).
    5. Explicitly rejects placeholder dashes, dots, waiting text, XXXXXX, etc.
    """
    if not result or not isinstance(result, dict):
        return False

    draw_date = str(result.get("draw_date", "")).strip()
    if draw_date != target_date:
        return False

    fp = str(result.get("first_prize", ""))
    l2 = str(result.get("last2", ""))

    placeholders = {
        "", "--", "---", "----", "-----", "------",
        "..", "...", "....", ".....", "......",
        "XX", "XXX", "XXXX", "XXXXX", "XXXXXX",
        "xx", "xxx", "xxxx", "xxxxx", "xxxxxx",
        "รอผล", "รอผลรางวัล", "รอยืนยัน", "รอการออกรางวัล", "กำลังออกผล"
    }
    if fp in placeholders or l2 in placeholders:
        return False
    if any(p in fp or p in l2 for p in ["รอผล", "รอยืนยัน"]):
        return False

    if not re.fullmatch(r"^\d{6}$", fp):
        return False

    if not re.fullmatch(r"^\d{2}$", l2):
        return False

    return True


# ── 1. Scrapers ───────────────────────────────────────

def fetch_thairath(target_date: str | None = None) -> dict | None:
    try:
        be_year = datetime.now().year + 543
        url = f"https://www.thairath.co.th/lottery/archive/{be_year}"
        soup = fetch_html(url)
        if not soup:
            return None
        rows = parse_thairath_page(soup, be_year)
        if not rows:
            return None

        if target_date:
            matching = next((r for r in rows if r.get("draw_date") == target_date), None)
            if not matching:
                return None
            latest = matching
        else:
            latest = max(rows, key=lambda r: r.get("draw_date", ""))

        first_prize = str(latest.get("first_prize", "")).strip()
        last2 = str(latest.get("last2", "")).strip()
        if not (re.fullmatch(r"^\d{6}$", first_prize) and re.fullmatch(r"^\d{2}$", last2)):
            return None

        return {
            "first_prize": first_prize,
            "front3": [latest.get("front3_1", ""), latest.get("front3_2", "")],
            "back3": [latest.get("back3_1", ""), latest.get("back3_2", "")],
            "last2": last2,
            "draw_date": latest.get("draw_date", ""),
            "source": "thairath"
        }
    except Exception as e:
        print(f"[WARN] fetch_thairath error: {e}")
        return None

def fetch_sanook(target_date: str | None = None) -> dict | None:
    try:
        res = requests.get("https://news.sanook.com/lotto/", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        hl = soup.find("div", class_="lotto-highlight")
        if not hl:
            return _extract_generic(soup.get_text(separator=" ", strip=True), "sanook")

        txt = hl.get_text()
        date_str = ""
        m_date = re.search(r'(\d{1,2})\s+([ก-๙\.]+)\s+(\d{4})', txt)
        if m_date:
            date_str = parse_thai_date_str(f"{m_date.group(1)} {m_date.group(2)} {m_date.group(3)}") or ""

        first_el = hl.find("strong", class_=lambda c: c and "first" in c)
        first_prize = first_el.get_text(strip=True) if first_el else ""

        front3, back3, last2 = [], [], ""
        for cell in hl.find_all("span", class_="lotto__cell"):
            c_txt = cell.get_text(separator=" ", strip=True)
            if "เลขหน้า" in c_txt or "หน้า 3" in c_txt:
                front3 = re.findall(r'\b(\d{3})\b', c_txt)[:2]
            elif "เลขท้าย 3" in c_txt or "ท้าย 3" in c_txt:
                back3 = re.findall(r'\b(\d{3})\b', c_txt)[:2]
            elif "เลขท้าย 2" in c_txt or "ท้าย 2" in c_txt:
                m = re.search(r'\b(\d{2})\b', c_txt)
                if m:
                    last2 = m.group(1)

        if re.fullmatch(r"^\d{6}$", first_prize) and re.fullmatch(r"^\d{2}$", last2):
            return {
                "first_prize": first_prize,
                "front3": front3 if len(front3) >= 2 else ["", ""],
                "back3": back3 if len(back3) >= 2 else ["", ""],
                "last2": last2,
                "draw_date": date_str,
                "source": "sanook"
            }
        return _extract_generic(soup.get_text(separator=" ", strip=True), "sanook")
    except Exception as e:
        print(f"[WARN] fetch_sanook error: {e}")
        return None

def fetch_kapook(target_date: str | None = None) -> dict | None:
    try:
        res = requests.get("https://lottery.kapook.com/", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        
        date_str = ""
        m_date = re.search(r'(\d{1,2})\s+([ก-๙\.]+)\s+(\d{4})', soup.get_text())
        if m_date:
            date_str = parse_thai_date_str(f"{m_date.group(1)} {m_date.group(2)} {m_date.group(3)}") or ""

        first_prize, last2 = "", ""
        front3, back3 = [], []

        for div in soup.find_all("div", class_="prize"):
            c_txt = div.get_text(separator=" ", strip=True)
            if "รางวัลที่ 1" in c_txt or "รางวัลที่1" in c_txt:
                m = re.search(r'\b(\d{6})\b', c_txt)
                if m:
                    first_prize = m.group(1)
            elif "เลขท้าย 2 ตัว" in c_txt:
                m = re.search(r'\b(\d{2})\b', c_txt)
                if m:
                    last2 = m.group(1)
            elif "เลขหน้า 3 ตัว" in c_txt:
                front3 = re.findall(r'\b(\d{3})\b', c_txt)[:2]
            elif "เลขท้าย 3 ตัว" in c_txt:
                back3 = re.findall(r'\b(\d{3})\b', c_txt)[:2]

        if re.fullmatch(r"^\d{6}$", first_prize) and re.fullmatch(r"^\d{2}$", last2):
            return {
                "first_prize": first_prize,
                "front3": front3 if len(front3) >= 2 else ["", ""],
                "back3": back3 if len(back3) >= 2 else ["", ""],
                "last2": last2,
                "draw_date": date_str,
                "source": "kapook"
            }
        return _extract_generic(soup.get_text(separator=" ", strip=True), "kapook")
    except Exception as e:
        print(f"[WARN] fetch_kapook error: {e}")
        return None

def _extract_generic(text: str, source_name: str) -> dict | None:
    """Best-effort regex extraction from raw page text with strict prize validation."""
    text_clean = text.replace(",", "").replace("\n", " ")
    
    date_str = ""
    m_date = re.search(r'(\d{1,2})\s+([\u0E00-\u0E7F\.]+)\s+(\d{4})', text)
    if m_date:
        d, m, y = m_date.groups()
        parsed = parse_thai_date_str(f"{d} {m} {y}")
        if parsed:
            date_str = parsed
    
    first_prize = ""
    for kw in ["รางวัลที่ 1", "รางวัลที่1"]:
        idx = text_clean.find(kw)
        if idx != -1:
            m = re.search(r'\b(\d{6})\b', text_clean[idx:idx+250])
            if m:
                first_prize = m.group(1)
                break
                
    front3 = []
    for kw in ["เลขหน้า 3 ตัว", "หน้า 3", "หน้า 3 ตัว"]:
        idx = text_clean.find(kw)
        if idx != -1:
            front3 = re.findall(r'\b(\d{3})\b', text_clean[idx:idx+250])[:2]
            if len(front3) >= 2:
                break
            
    back3 = []
    for kw in ["เลขท้าย 3 ตัว", "ท้าย 3", "ท้าย 3 ตัว"]:
        idx = text_clean.find(kw)
        if idx != -1:
            back3 = re.findall(r'\b(\d{3})\b', text_clean[idx:idx+250])[:2]
            if len(back3) >= 2:
                break
            
    last2 = ""
    for kw in ["เลขท้าย 2 ตัว", "ท้าย 2", "ท้าย 2 ตัว"]:
        idx = text_clean.find(kw)
        if idx != -1:
            m = re.search(r'\b(\d{2})\b', text_clean[idx:idx+250])
            if m:
                last2 = m.group(1)
                break
                
    if re.fullmatch(r"^\d{6}$", first_prize) and re.fullmatch(r"^\d{2}$", last2):
        return {
            "first_prize": first_prize,
            "front3": front3 if len(front3) >= 2 else ["", ""],
            "back3": back3 if len(back3) >= 2 else ["", ""],
            "last2": last2,
            "draw_date": date_str,
            "source": source_name
        }
    return None


# ── 2. Collect & Validate ──────────────────────────────────────────

def collect_and_validate(target_date: str | None = None) -> dict | None:
    if not target_date:
        target_date = get_expected_draw_date()

    print(f"[INFO] Target draw date: {target_date}")
    raw_results = []

    fetchers = [
        ("thairath", fetch_thairath),
        ("sanook", fetch_sanook),
        ("kapook", fetch_kapook),
    ]
    for name, fetcher in fetchers:
        try:
            res = fetcher(target_date)
        except TypeError:
            res = fetcher()
        if res:
            raw_results.append(res)

    if not raw_results:
        print(f"[INFO] All fetchers returned no data for target date {target_date}.")
        return None

    valid_results = []
    for r in raw_results:
        if is_valid_draw_result(r, target_date):
            valid_results.append(r)
        else:
            r_source = r.get("source", "unknown")
            r_date = r.get("draw_date") or "-"
            r_fp = r.get("first_prize") or "-"
            r_l2 = r.get("last2") or "-"
            print(f"[INFO] Source '{r_source}' rejected (date={r_date}, 1st={r_fp}, last2={r_l2}; target={target_date})")

    if not valid_results:
        print(f"[INFO] No valid results matching target date {target_date} from any source.")
        return None

    signatures = {}
    for r in valid_results:
        sig = f"{r['first_prize']}|{r['last2']}"
        signatures.setdefault(sig, []).append(r)

    for sig, matching_results in signatures.items():
        if len(matching_results) >= 2:
            sources = "+".join([m["source"] for m in matching_results])
            print(f"[INFO] Consensus reached! Matching sources: {sources} -> {sig} for {target_date}")
            best_match = max(matching_results, key=lambda m: (
                len([x for x in m.get("front3", []) if x]),
                len([x for x in m.get("back3", []) if x])
            ))
            final_result = dict(best_match)
            final_result["source"] = sources
            final_result["draw_date"] = target_date
            return final_result

    print(f"[WARN] Sources disagree or insufficient consensus (< 2 matching sources) for {target_date}.")
    for r in valid_results:
        print(f" -> {r['source'].ljust(10)}: {r.get('draw_date')} | 1st: {r['first_prize']} | Last2: {r['last2']}")
    return None


# ── 3. Append Dataset ─────────────────────────────────

def append_dataset(result: dict) -> bool:
    """
    Append verified draw result to CSV dataset.
    Returns True if a new draw was appended; False if already present or invalid.
    """
    if not CSV_PATH.exists():
        print(f"[ERROR] Dataset path does not exist: {CSV_PATH}")
        return False

    fieldnames = [
        "draw_date", "first_prize",
        "front3_1", "front3_2", "back3_1", "back3_2", "last2",
        "digit1", "digit2", "digit3", "digit4", "digit5", "digit6",
    ]
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        rows = {
            row["draw_date"]: row
            for row in csv.DictReader(f)
            if row.get("draw_date")
        }

    date = result["draw_date"]

    if date in rows:
        print(f"[INFO] Draw {date} already exists in {CSV_PATH.name}. Skipping append.")
        return False

    first_prize = str(result.get("first_prize", "")).strip()
    if not re.fullmatch(r"^\d{6}$", first_prize):
        print(f"[ERROR] Cannot append invalid first_prize: '{first_prize}'")
        return False

    last2 = str(result.get("last2", "")).strip()
    if not re.fullmatch(r"^\d{2}$", last2):
        print(f"[ERROR] Cannot append invalid last2: '{last2}'")
        return False

    front3 = result.get("front3", [])
    back3 = result.get("back3", [])

    row = {
        "draw_date": date,
        "first_prize": first_prize,
        "front3_1": front3[0] if len(front3) > 0 else "",
        "front3_2": front3[1] if len(front3) > 1 else "",
        "back3_1": back3[0] if len(back3) > 0 else "",
        "back3_2": back3[1] if len(back3) > 1 else "",
        "last2": last2,
    }
    row.update({f"digit{i + 1}": first_prize[i] for i in range(6)})
    rows[date] = row

    sorted_rows = sorted(rows.values(), key=lambda r: r.get("draw_date", ""), reverse=True)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted_rows)

    print(f"[INFO] Dataset updated -> {CSV_PATH.name} (Verified via: {result.get('source')})")
    return True


# ── 4. Metrics & Pipeline Trigger ─────────────────────

def get_draw_count() -> int:
    if not CSV_PATH.exists(): return 0
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))

def update_metrics(result: dict) -> None:
    date = result["draw_date"]
    actual = result.get("first_prize", "")
    
    if not actual: return
    
    if HISTORY_JSON.exists():
        data = json.loads(HISTORY_JSON.read_text(encoding="utf-8"))
        updated = False
        for entry in data:
            if entry.get("target_date") == date and not entry.get("actual_result"):
                best_hits, best_cand = 0, ""
                for cand in entry.get("candidates", []):
                    pred = cand.get("number", "")
                    hits = sum(1 for a, b in zip(pred, actual) if a == b)
                    if hits > best_hits: best_hits, best_cand = hits, pred
                entry["actual_result"] = actual
                entry["accuracy"] = {
                    "best": {"candidate": best_cand, "positional_hits": best_hits, "digit_hits": len(set(best_cand) & set(actual))},
                    "any_exact_match": actual in [c.get("number") for c in entry.get("candidates", [])]
                }
                updated = True
        if updated:
            HISTORY_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    if PERF_JSON.exists() and HISTORY_JSON.exists():
        data = [e for e in json.loads(HISTORY_JSON.read_text(encoding="utf-8")) if e.get("accuracy")]
        if data:
            n = len(data)
            avg_pos = sum(e["accuracy"]["best"]["positional_hits"] for e in data) / n
            avg_dig = sum(e["accuracy"]["best"]["digit_hits"] for e in data) / n
            exact   = sum(1 for e in data if e["accuracy"].get("any_exact_match"))
            perf = {
                "updated": datetime.now().isoformat(),
                "evaluated": n,
                "avg_positional_hits": round(avg_pos, 3),
                "avg_digit_hits": round(avg_dig, 3),
                "exact_matches": exact,
            }
            try:
                from analytics.performance_analyzer import PerformanceAnalyzer
                analyzer = PerformanceAnalyzer()
                analyzer.entries = data
                analyzer.analyze()
                for key in ("model_score", "hit_rate", "digit_accuracy"):
                    if key in analyzer.results:
                        perf[key] = analyzer.results[key]
            except Exception as e:
                print(f"[WARN] Could not enrich performance.json: {e}")
            PERF_JSON.write_text(json.dumps(perf, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Main ──────────────────────────────────────────────

def run(target_date: str | None = None, force: bool = False, exit_on_finish: bool = True) -> bool:
    if not target_date:
        target_date = get_expected_draw_date()

    print(f"[INFO] Starting result fetcher for draw date: {target_date}")
    result = collect_and_validate(target_date)

    if not result:
        print(f"[INFO] Results for {target_date} are unannounced or incomplete. Exiting cleanly (code 0).")
        set_github_output("has_new_draw", "false")
        if exit_on_finish:
            sys.exit(0)
        return False

    is_new = append_dataset(result)
    if not is_new and not force:
        print(f"[INFO] Draw {target_date} already recorded in {CSV_PATH.name}. Exiting cleanly without retraining.")
        set_github_output("has_new_draw", "false")
        if exit_on_finish:
            sys.exit(0)
        return False

    set_github_output("has_new_draw", "true")
    print(f"[INFO] Total draws: {get_draw_count()}")
    print(f"[INFO] Updating metrics for verified draw {target_date}...")
    update_metrics(result)

    print("[INFO] Running prediction pipeline...")
    subprocess.run(["python", str(BASE / "api" / "run_pipeline.py")], cwd=str(BASE), check=True)
    print("[INFO] Predictions and pipeline cache updated successfully.")
    if exit_on_finish:
        sys.exit(0)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-fetch Thai Lottery Results & Trigger Pipeline")
    parser.add_argument("--date", type=str, default=None, help="Target draw date (YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help="Force metrics update and pipeline retrain even if draw exists")
    args = parser.parse_args()

    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"[ERROR] Invalid date format for --date: '{args.date}'. Expected YYYY-MM-DD.")
            sys.exit(1)

    run(target_date=args.date, force=args.force, exit_on_finish=True)
