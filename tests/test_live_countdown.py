"""
tests/test_live_countdown.py

Automated Test Suite for the Real-Time Auto-Fetch & Dual Calendar Countdown Engine.
Tests:
1. Official Thai lottery calendar shift rules (Dec 30, Jan 17, May 2, standard 1st and 16th).
2. Live draw broadcasting window detection (14:30 - 16:30 ICT).
3. JavaScript module integrity and node execution of assets/live_countdown.js.
4. Data parity and next_draw metadata in hopper_3d_data.json.
"""

import json
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
JS_ENGINE = REPO_ROOT / "assets" / "live_countdown.js"
DASHBOARD_JS_ENGINE = REPO_ROOT / "dashboard" / "assets" / "live_countdown.js"
HOPPER_DATA = REPO_ROOT / "database" / "predictions" / "hopper_3d_data.json"
DASHBOARD_HOPPER = REPO_ROOT / "dashboard" / "hopper_3d_data.json"

ICT = timezone(timedelta(hours=7))


# ── 1. File Presence & Parity ───────────────────────────────────────

def test_live_countdown_js_exists_and_mirrored():
    """Verify live_countdown.js exists in root assets and dashboard/assets with matching content."""
    assert JS_ENGINE.exists(), "assets/live_countdown.js must exist"
    assert DASHBOARD_JS_ENGINE.exists(), "dashboard/assets/live_countdown.js must exist"
    assert JS_ENGINE.read_text(encoding="utf-8") == DASHBOARD_JS_ENGINE.read_text(encoding="utf-8")


def test_hopper_data_contains_next_draw_meta():
    """Verify hopper_3d_data.json contains next_draw object with draw_date and iso_target."""
    assert HOPPER_DATA.exists()
    data = json.loads(HOPPER_DATA.read_text(encoding="utf-8"))
    meta = data.get("meta", {})
    assert "next_draw" in meta, "meta must contain 'next_draw' block"
    nd = meta["next_draw"]
    assert "draw_date" in nd
    assert "iso_target" in nd
    assert "thai_formatted" in nd
    assert "14:30:00" in nd["iso_target"]


# ── 2. JavaScript Engine Node.js Execution Tests ────────────────────

def run_node_eval(js_code: str) -> str:
    """Helper to evaluate JS snippet importing live_countdown.js via node."""
    full_code = f"""
    const engine = require('{JS_ENGINE.as_posix()}');
    {js_code}
    """
    res = subprocess.run(
        ["node", "-e", full_code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(REPO_ROOT),
        timeout=10
    )
    assert res.returncode == 0, f"Node eval failed: {res.stderr}"
    return res.stdout.strip()


def test_js_engine_export_contract():
    """Verify the module exports expected functions: isOfficialDrawDay, getNextDrawDate, isDrawWindow, createEngine."""
    res = run_node_eval("""
    const keys = Object.keys(engine);
    console.log(JSON.stringify(keys));
    """)
    keys = json.loads(res)
    assert "isOfficialDrawDay" in keys
    assert "getNextDrawDate" in keys
    assert "isDrawWindow" in keys
    assert "createEngine" in keys


@pytest.mark.parametrize("y,m,d,expected", [
    (2026, 1, 1, False),    # Jan 1 skipped
    (2026, 1, 16, False),   # Jan 16 skipped (Teacher's Day)
    (2026, 1, 17, True),    # Jan 17 official draw
    (2026, 5, 1, False),    # May 1 skipped (Labour Day)
    (2026, 5, 2, True),     # May 2 official draw
    (2026, 12, 30, True),   # Dec 30 official draw
    (2026, 12, 31, False),  # Dec 31 not draw day
    (2026, 9, 16, True),    # Standard 16th
    (2026, 10, 1, True),    # Standard 1st
    (2026, 10, 2, False),   # Non draw day
])
def test_js_calendar_official_draw_day_rules(y, m, d, expected):
    """Verify JS isOfficialDrawDay matches official government lottery calendar rules."""
    js = f"""
    const d = new Date({y}, {m - 1}, {d});
    console.log(engine.isOfficialDrawDay(d));
    """
    res = run_node_eval(js)
    assert res == str(expected).lower()


def test_js_next_draw_rollover_after_sep16():
    """Verify that after Sep 16 draw, next draw rolls over to Oct 1 at 14:30 ICT."""
    js = """
    // Reference date: Sep 16, 2026 at 17:00 ICT (draw finished)
    const ref = new Date('2026-09-16T17:00:00+07:00');
    const next = engine.getNextDrawDate(ref);
    console.log(JSON.stringify(next));
    """
    res = run_node_eval(js)
    data = json.loads(res)
    assert data["drawDayStr"] == "2026-10-01"
    assert "2026-10-01T14:30:00" in data["isoString"]
    assert "1 ตุลาคม 2569" in data["thaiFormatted"]


def test_js_next_draw_rollover_at_year_end():
    """Verify that on Dec 17, next draw is Dec 30 (not Jan 1)."""
    js = """
    const ref = new Date('2026-12-17T10:00:00+07:00');
    const next = engine.getNextDrawDate(ref);
    console.log(JSON.stringify(next));
    """
    res = run_node_eval(js)
    data = json.loads(res)
    assert data["drawDayStr"] == "2026-12-30"


def test_js_draw_window_detection():
    """Verify isDrawWindow detects 14:30 - 16:30 ICT on draw days correctly."""
    # 1. On draw day inside window: 14:45 ICT -> True
    js_true = """
    const inWindow = new Date(2026, 8, 16, 14, 45, 0);
    console.log(engine.isDrawWindow(inWindow));
    """
    assert run_node_eval(js_true) == "true"

    # 2. On draw day before window: 11:00 ICT -> False
    js_false_early = """
    const early = new Date(2026, 8, 16, 11, 0, 0);
    console.log(engine.isDrawWindow(early));
    """
    assert run_node_eval(js_false_early) == "false"

    # 3. On draw day after window: 17:00 ICT -> False
    js_false_late = """
    const late = new Date(2026, 8, 16, 17, 0, 0);
    console.log(engine.isDrawWindow(late));
    """
    assert run_node_eval(js_false_late) == "false"

    # 4. On non-draw day at 14:45 ICT -> False
    js_false_not_draw_day = """
    const notDrawDay = new Date(2026, 8, 15, 14, 45, 0);
    console.log(engine.isDrawWindow(notDrawDay));
    """
    assert run_node_eval(js_false_not_draw_day) == "false"
