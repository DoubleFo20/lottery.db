"""tests/test_manager_dashboard.py
Tests for the AI Manager Control Center (manager.html) and Dry Spell Advisory System:
- DOM elements verification (Live countdown, Latest result, Full spectrum, Consecutive miss alert)
- Dynamic action prompt generator and 5-step remediation playbook
- SHA-256 parity between root manager.html and dashboard/manager.html
- Persistent workspace rule existence (.agents/rules/dry_spell_remediation.md)
"""

import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_MANAGER = REPO_ROOT / "manager.html"
DASHBOARD_MANAGER = REPO_ROOT / "dashboard" / "manager.html"
RULE_FILE = REPO_ROOT / ".agents" / "rules" / "dry_spell_remediation.md"


def test_manager_html_sha256_parity():
    """Verify that root manager.html and dashboard/manager.html are 100% byte-for-byte identical."""
    assert ROOT_MANAGER.exists(), "Root manager.html must exist"
    assert DASHBOARD_MANAGER.exists(), "Dashboard manager.html must exist"
    
    h_root = hashlib.sha256(ROOT_MANAGER.read_bytes()).hexdigest()
    h_dash = hashlib.sha256(DASHBOARD_MANAGER.read_bytes()).hexdigest()
    assert h_root == h_dash, f"SHA-256 mismatch: root={h_root} vs dash={h_dash}"


def test_manager_html_dom_elements():
    """Verify that manager.html contains all required DOM structures and scripts."""
    content = ROOT_MANAGER.read_text(encoding="utf-8")
    
    # 1. Scripts
    assert "assets/live_countdown.js" in content, "Must include live_countdown.js"
    
    # 2. Countdown and Results
    assert "manager-countdown-timer" in content, "Must contain manager-countdown-timer"
    assert "cd-days" in content, "Must contain cd-days"
    assert "cd-hours" in content, "Must contain cd-hours"
    assert "cd-mins" in content, "Must contain cd-mins"
    assert "cd-secs" in content, "Must contain cd-secs"
    assert "res-first-prize" in content, "Must contain res-first-prize"
    assert "res-last2" in content, "Must contain res-last2"
    
    # 3. Consecutive Miss Alert and Action Prompt
    assert "consecutive-miss-alert-box" in content, "Must contain consecutive-miss-alert-box"
    assert "setConsecutiveThreshold" in content, "Must contain setConsecutiveThreshold function"
    assert "renderConsecutiveMissAlert" in content, "Must contain renderConsecutiveMissAlert function"
    assert "copyAgentActionPrompt" in content, "Must contain copyAgentActionPrompt function"
    
    # 4. Full Spectrum Predictions
    assert "fs-jackpot-num" in content, "Must contain fs-jackpot-num"
    assert "fs-jackpot-neighbors" in content, "Must contain fs-jackpot-neighbors"
    assert "fs-top2-pairs" in content, "Must contain fs-top2-pairs"
    assert "fs-top3-box" in content, "Must contain fs-top3-box"
    assert "fs-banker-digits" in content, "Must contain fs-banker-digits"
    assert "renderFullSpectrum" in content, "Must contain renderFullSpectrum function"


def test_consecutive_miss_prompt_contents():
    """Verify that copyAgentActionPrompt includes the 5-step remediation playbook."""
    content = ROOT_MANAGER.read_text(encoding="utf-8")
    
    # 5 Strategic points in the prompt
    assert "Root Cause Analysis" in content
    assert "Dynamic Weight Tuning" in content
    assert "Beam & Filter Expansion" in content
    assert "Hedging Staking Pivot" in content
    assert "Verification & Retest" in content
    assert "database/predictions/ensemble_weights.json" in content
    assert "ensemble_model/predictor.py" in content
    assert "Banker Core" in content


def test_dry_spell_remediation_rule_exists():
    """Verify that the persistent workspace rule file exists and conforms to governance."""
    assert RULE_FILE.exists(), "dry_spell_remediation.md must exist in .agents/rules/"
    rule_content = RULE_FILE.read_text(encoding="utf-8")
    assert "dry-spell-remediation" in rule_content
    assert "Root Cause & Drift Analysis" in rule_content
    assert "Dynamic Weight Recalibration" in rule_content
    assert "Search Space & Diversity Expansion" in rule_content
    assert "Hedging Portfolio Reallocation" in rule_content
    assert "Retraining, Verification & Deployment" in rule_content
