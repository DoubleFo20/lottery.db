"""analytics/result_fetcher.py — Auto-fetch Thai Lottery Results & Trigger Pipeline"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import csv
import json
import sys
import subprocess
import re
from datetime import datetime
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


# ── 1. Scrapers ───────────────────────────────────────

def fetch_thairath() -> dict | None:
    be_year = datetime.now().year + 543
    url = f"https://www.thairath.co.th/lottery/archive/{be_year}"
    soup = fetch_html(url)
    if not soup: return None
    rows = parse_thairath_page(soup, be_year)
    if not rows: return None
    latest = max(rows, key=lambda r: r["draw_date"])
    return {
        "first_prize": latest.get("first_prize", ""),
        "front3": [latest.get("front3_1", ""), latest.get("front3_2", "")],
        "back3": [latest.get("back3_1", ""), latest.get("back3_2", "")],
        "last2": latest.get("last2", ""),
        "draw_date": latest.get("draw_date", ""),
        "source": "thairath"
    }

def fetch_sanook() -> dict | None:
    try:
        res = requests.get("https://news.sanook.com/lotto/", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        return _extract_generic(soup.get_text(separator=" ", strip=True), "sanook")
    except Exception as e:
        print(f"[WARN] fetch_sanook error: {e}")
        return None

def fetch_kapook() -> dict | None:
    try:
        res = requests.get("https://lottery.kapook.com/", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        return _extract_generic(soup.get_text(separator=" ", strip=True), "kapook")
    except Exception as e:
        print(f"[WARN] fetch_kapook error: {e}")
        return None

def _extract_generic(text: str, source_name: str) -> dict | None:
    """Best-effort regex extraction from raw page text."""
    text_clean = text.replace(",", "").replace("\n", " ")
    
    date_str = ""
    m_date = re.search(r'(\d{1,2})\s+([ก-ฮ\.]+)\s+(\d{4})', text)
    if m_date:
        d, m, y = m_date.groups()
        parsed = parse_thai_date(f"{d} {m} {y}")
        if parsed: date_str = parsed
    
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
            if len(front3) >= 2: break
            
    back3 = []
    for kw in ["เลขท้าย 3 ตัว", "ท้าย 3", "ท้าย 3 ตัว"]:
        idx = text_clean.find(kw)
        if idx != -1:
            back3 = re.findall(r'\b(\d{3})\b', text_clean[idx:idx+250])[:2]
            if len(back3) >= 2: break
            
    last2 = ""
    for kw in ["เลขท้าย 2 ตัว", "ท้าย 2", "ท้าย 2 ตัว"]:
        idx = text_clean.find(kw)
        if idx != -1:
            m = re.search(r'\b(\d{2})\b', text_clean[idx:idx+250])
            if m:
                last2 = m.group(1)
                break
                
    if first_prize and len(first_prize) == 6:
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

def collect_and_validate() -> dict | None:
    results = []
    
    for fetcher in [fetch_thairath, fetch_sanook, fetch_kapook]:
        res = fetcher()
        if res: results.append(res)
    
    if not results:
        print("[ERROR] All fetchers failed to return data.")
        return None
        
    # Group by prize signature. Some pages expose the right prize numbers but
    # hide the draw date in markup we cannot reliably parse.
    signatures = {}
    for r in results:
        sig = f"{r['first_prize']}|{r['last2']}"
        signatures.setdefault(sig, []).append(r)
        
    # Validate result consistency: If at least two sources match → accept result.
    for sig, matching_results in signatures.items():
        if len(matching_results) >= 2:
            sources = "+".join([m["source"] for m in matching_results])
            print(f"[INFO] Consensus reached! Matching sources: {sources} -> {sig}")
            
            dated = [m for m in matching_results if m.get("draw_date")]
            if not dated:
                print("[WARN] Matching sources did not provide a parseable draw date.")
                continue

            # Prefer Thairath archive dates, then newest parseable date.
            best_match = next((m for m in dated if m.get("source") == "thairath"), None)
            if best_match is None:
                best_match = max(dated, key=lambda m: m.get("draw_date", ""))
            best_match["source"] = sources
            return best_match
            
    # Condition: If sources disagree → log warning but do not write dataset.
    print("[WARN] Sources disagree! No consensus reached. Validation failed.")
    for r in results:
        print(f" -> {r['source'].ljust(10)}: {r.get('draw_date') or '-'} | 1st: {r['first_prize']} | Last2: {r['last2']}")
    return None


# ── 3. Append Dataset ─────────────────────────────────

def append_dataset(result: dict):
    if not CSV_PATH.exists(): return

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
        print(f"[INFO] Draw {date} already exists. Skipping append.")
        return

    first_prize = result.get("first_prize", "").zfill(6)[:6]
    row = {
        "draw_date": date,
        "first_prize": first_prize,
        "front3_1": result["front3"][0] if len(result.get("front3", [])) > 0 else "",
        "front3_2": result["front3"][1] if len(result.get("front3", [])) > 1 else "",
        "back3_1": result["back3"][0] if len(result.get("back3", [])) > 0 else "",
        "back3_2": result["back3"][1] if len(result.get("back3", [])) > 1 else "",
        "last2": result.get("last2", ""),
    }
    row.update({f"digit{i + 1}": first_prize[i] for i in range(6)})
    rows[date] = row

    sorted_rows = sorted(rows.values(), key=lambda r: r.get("draw_date", ""), reverse=True)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted_rows)

    print(f"[INFO] Dataset updated -> {CSV_PATH.name} (Verified via: {result.get('source')})")


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

def run():
    result = collect_and_validate()
    if not result:
        return print("[ERROR] Validation failed. Skipped dataset insertion and pipeline.")
        
    append_dataset(result)
    print(f"[INFO] Total draws: {get_draw_count()}")
    
    update_metrics(result)
    
    print("[INFO] Running prediction pipeline...")
    subprocess.run(["python", str(BASE / "api" / "run_pipeline.py")], cwd=str(BASE))
    print("[INFO] Predictions updated")


if __name__ == "__main__":
    run()
