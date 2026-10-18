"""
tests/test_ui_qa_regressions.py
Regression tests for:
1. Zero duplicate DOM IDs across all static HTML templates.
2. Mirror parity (100% byte-for-byte SHA-256 match) between root and dashboard/ files.
3. Bilingual i18n dictionaries integrity.
4. Statistical panel elements and data files integrity.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def get_file_sha256(rel_path: str) -> str:
    path = ROOT / rel_path
    assert path.exists(), f"File does not exist: {rel_path}"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_mirror_parity():
    pairs = [
        ("index.html", "dashboard/index.html"),
        ("strategy.html", "dashboard/strategy.html"),
        ("strategy.html", "index.html"),
        ("performance.html", "dashboard/performance.html"),
        ("manager.html", "dashboard/manager.html"),
        ("3d.html", "dashboard/3d.html"),
        ("mobile-wallet.html", "dashboard/mobile-wallet.html"),
        ("assets/css/premium-theme.css", "dashboard/assets/css/premium-theme.css"),
        ("assets/js/nav-component.js", "dashboard/assets/js/nav-component.js"),
        ("assets/js/i18n.js", "dashboard/assets/js/i18n.js"),
    ]
    for p1, p2 in pairs:
        h1 = get_file_sha256(p1)
        h2 = get_file_sha256(p2)
        assert h1 == h2, f"Mirror parity mismatch: {p1} ({h1[:8]}) != {p2} ({h2[:8]})"


def test_no_duplicate_dom_ids():
    html_files = [
        "strategy.html",
        "manager.html",
        "performance.html",
        "3d.html",
        "mobile-wallet.html",
        "dashboard/strategy.html",
        "dashboard/manager.html",
        "dashboard/performance.html",
        "dashboard/3d.html",
        "dashboard/mobile-wallet.html",
    ]
    id_pattern = re.compile(r'\bid=["\']([^"\']+)["\']')
    for rel in html_files:
        path = ROOT / rel
        content = path.read_text(encoding="utf-8")
        seen = set()
        dups = []
        for match in id_pattern.finditer(content):
            dom_id = match.group(1)
            if dom_id in seen:
                dups.append(dom_id)
            else:
                seen.add(dom_id)
        assert not dups, f"Duplicate DOM IDs in {rel}: {dups}"


def test_i18n_dictionaries_completeness():
    th_path = ROOT / "i18n" / "th.json"
    en_path = ROOT / "i18n" / "en.json"
    assert th_path.exists()
    assert en_path.exists()

    th = json.loads(th_path.read_text(encoding="utf-8"))
    en = json.loads(en_path.read_text(encoding="utf-8"))

    for sec in ["meta", "nav", "results", "countdown", "predictions", "analytics", "manager", "performance", "showcase_3d"]:
        assert sec in th, f"Missing section '{sec}' in th.json"
        assert sec in en, f"Missing section '{sec}' in en.json"

    assert "run_pipeline" in th["manager"]
    assert "run_pipeline" in en["manager"]
    assert "scientific_disclaimer" in th["performance"]
    assert "scientific_disclaimer" in en["performance"]


def test_backtest_comparative_data_file():
    comp_path = ROOT / "database" / "backtest" / "comparative_report.json"
    assert comp_path.exists(), "comparative_report.json must exist"
    data = json.loads(comp_path.read_text(encoding="utf-8"))
    assert "ensemble" in data
    ens = data["ensemble"]
    assert ens["attempted_draws"] == 20
    assert ens["successful_draws"] == 20
    assert ens["prediction_failures"] == 0
    assert "statistical_uncertainty" in ens
    assert "wilson_ci_95" in ens["statistical_uncertainty"]
