"""tests/test_auto_update_pipeline.py
End-to-End Integration Tests for Lottery Pipeline:
- Pipeline prediction engine execution and pipeline_cache.json structure
- Accuracy evaluation and performance.json metrics calculation
- Node.js 3D hopper data generation (scripts/prep-3d-data.js)
- Dashboard HTML and asset synchronization parity
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_CACHE = REPO_ROOT / "database" / "predictions" / "pipeline_cache.json"
HOPPER_DATA = REPO_ROOT / "database" / "predictions" / "hopper_3d_data.json"
DASHBOARD_HOPPER = REPO_ROOT / "dashboard" / "hopper_3d_data.json"
PERF_JSON = REPO_ROOT / "performance.json"


@pytest.fixture(scope="module", autouse=True)
def preserve_tracked_prediction_files():
    """Backup tracked json prediction and hopper data files before tests and restore afterwards."""
    backups = {}
    for path in [PIPELINE_CACHE, HOPPER_DATA, DASHBOARD_HOPPER]:
        if path.exists():
            backups[path] = path.read_bytes()
    yield
    for path, data in backups.items():
        try:
            path.write_bytes(data)
        except Exception:
            pass


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


# ── 1. Pipeline Execution & Prediction Cache Schema ─────────────────

def test_pipeline_cache_file_exists_and_valid_json():
    """Verify that database/predictions/pipeline_cache.json exists and is valid JSON."""
    assert PIPELINE_CACHE.exists(), f"Pipeline cache file missing at {PIPELINE_CACHE}"
    data = json.loads(PIPELINE_CACHE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("status") == "ok"
    assert "candidates" in data
    assert isinstance(data["candidates"], list)
    assert len(data["candidates"]) > 0


def test_pipeline_cache_candidate_schema_fields():
    """Verify each candidate in pipeline_cache.json contains all required fields."""
    data = json.loads(PIPELINE_CACHE.read_text(encoding="utf-8"))
    for cand in data["candidates"]:
        assert "number" in cand, "Candidate must have 'number'"
        assert len(cand["number"]) == 6, f"Candidate number must be 6 digits, got {cand['number']}"
        assert cand["number"].isdigit(), f"Candidate number must be numeric: {cand['number']}"
        assert "score" in cand
        assert "confidence" in cand


def test_pipeline_runner_executes_successfully():
    """Execute api/run_pipeline.py with a small window and verify zero exit code."""
    cmd = [sys.executable, "api/run_pipeline.py", "--top", "3", "--window", "20"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30)
    assert res.returncode == 0, f"run_pipeline.py failed: {res.stderr}"
    assert PIPELINE_CACHE.exists()


# ── 2. Metrics & Performance Evaluation ─────────────────────────────

def test_metrics_evaluation_logic_on_mock_prediction(tmp_path):
    """Verify update_metrics evaluates positional and digit hits correctly."""
    from analytics.result_fetcher import update_metrics

    test_history = tmp_path / "prediction_history.json"
    test_perf = tmp_path / "performance.json"

    initial_history = [
        {
            "target_date": "2026-10-01",
            "candidates": [
                {"number": "730640", "score": 0.95},
                {"number": "123456", "score": 0.80}
            ]
        }
    ]
    test_history.write_text(json.dumps(initial_history, ensure_ascii=False), encoding="utf-8")
    test_perf.write_text("{}", encoding="utf-8")

    result = {
        "draw_date": "2026-10-01",
        "first_prize": "730640"
    }

    import analytics.result_fetcher as rf
    with patch.object(rf, "HISTORY_JSON", test_history), \
         patch.object(rf, "PERF_JSON", test_perf):
        update_metrics(result)

    updated_history = json.loads(test_history.read_text(encoding="utf-8"))
    entry = updated_history[0]
    assert entry.get("actual_result") == "730640"
    assert entry["accuracy"]["best"]["positional_hits"] == 6
    assert entry["accuracy"]["best"]["digit_hits"] == 5  # unique digits: 7, 3, 0, 6, 4 (5 unique)
    assert entry["accuracy"]["any_exact_match"] is True


# ── 3. Node.js 3D Hopper Data Generation ────────────────────────────

def test_node_prep_3d_script_execution():
    """Execute node scripts/prep-3d-data.js and verify hopper_3d_data.json generation."""
    cmd = ["node", "scripts/prep-3d-data.js"]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        timeout=15
    )
    assert res.returncode == 0, f"prep-3d-data.js failed: {res.stderr}"

    assert HOPPER_DATA.exists(), "database/predictions/hopper_3d_data.json must exist"
    data = json.loads(HOPPER_DATA.read_text(encoding="utf-8"))
    assert "meta" in data, "Hopper data must contain 'meta' block"
    assert "generated_at" in data["meta"], "'meta' block must contain 'generated_at'"
    assert "balls" in data
    assert len(data["balls"]) == 40, f"Expected 40 hopper balls, got {len(data['balls'])}"


def test_hopper_data_dashboard_mirroring():
    """Verify hopper_3d_data.json is synchronized to dashboard/hopper_3d_data.json."""
    assert DASHBOARD_HOPPER.exists(), "dashboard/hopper_3d_data.json must exist"
    assert sha256_file(HOPPER_DATA) == sha256_file(DASHBOARD_HOPPER), (
        "Hopper 3D data in database/predictions and dashboard must have matching hashes"
    )


# ── 4. Dashboard Mirror Synchronization Parity ──────────────────────

def test_index_html_identical_to_strategy_html():
    """Verify index.html and strategy.html in root are byte-for-byte identical."""
    idx = REPO_ROOT / "index.html"
    strat = REPO_ROOT / "strategy.html"
    assert idx.exists() and strat.exists()
    assert sha256_file(idx) == sha256_file(strat), (
        "index.html and strategy.html must be identical"
    )


def test_dashboard_mirror_files_match_root_files():
    """Verify root HTML dashboards match their counterparts in dashboard/ directory."""
    pairs = [
        ("index.html", "dashboard/strategy.html"),
        ("manager.html", "dashboard/manager.html"),
        ("performance.html", "dashboard/performance.html"),
        ("3d.html", "dashboard/3d.html"),
    ]
    for root_rel, dash_rel in pairs:
        root_path = REPO_ROOT / root_rel
        dash_path = REPO_ROOT / dash_rel
        assert root_path.exists(), f"Missing root file {root_rel}"
        assert dash_path.exists(), f"Missing dashboard file {dash_rel}"
        assert sha256_file(root_path) == sha256_file(dash_path), (
            f"Hash mismatch between {root_rel} and {dash_rel}"
        )
