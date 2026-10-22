"""tests/test_mobile_wallet.py
Comprehensive verification test suite for the Lottery Companion Hub (mobile-wallet.html):
- SHA-256 byte-for-byte parity between root mobile-wallet.html and dashboard/mobile-wallet.html
- Elimination of fictional banking entities (Spotify, Alice, salary, Euro balance, bank transfers)
- Presence of lottery-specific companion structures (Prediction Portfolio, Saved Tickets, Draw Checker, Expense Logger)
- XSS sanitization and keyboard/gesture controls
"""

import hashlib
import re
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_WALLET = REPO_ROOT / "mobile-wallet.html"
DASHBOARD_WALLET = REPO_ROOT / "dashboard" / "mobile-wallet.html"


def test_mobile_wallet_sha256_parity():
    """Verify that root mobile-wallet.html and dashboard/mobile-wallet.html are 100% byte-for-byte identical."""
    assert ROOT_WALLET.exists(), "Root mobile-wallet.html must exist"
    assert DASHBOARD_WALLET.exists(), "Dashboard mobile-wallet.html must exist"

    h_root = hashlib.sha256(ROOT_WALLET.read_bytes()).hexdigest()
    h_dash = hashlib.sha256(DASHBOARD_WALLET.read_bytes()).hexdigest()
    assert h_root == h_dash, f"SHA-256 mismatch: root={h_root} vs dash={h_dash}"


def test_zero_fictional_banking_artifacts():
    """Verify that fake banking data (Spotify, Alice, NovaTech, salary, Euro) has been completely removed."""
    content = ROOT_WALLET.read_text(encoding="utf-8")

    assert "Spotify" not in content, "Fictional Spotify subscription must be removed"
    assert "Alice" not in content, "Fictional contact Alice must be removed"
    assert "NovaTech" not in content, "Fictional employer NovaTech must be removed"
    assert "Salary" not in content, "Fictional salary transfer must be removed"
    assert "€12,480" not in content, "Fictional Euro balance must be removed"


def test_lottery_companion_dom_elements():
    """Verify that mobile-wallet.html contains all essential Lottery Companion structures."""
    content = ROOT_WALLET.read_text(encoding="utf-8")

    # 1. iOS Shell & Dynamic Island
    assert "ios-status-bar" in content, "Must contain ios-status-bar"
    assert "status-clock" in content, "Must contain status-clock"
    assert "dynamic-island" in content, "Must contain dynamic-island"
    assert "battery-pill" in content, "Must contain battery-pill"

    # 2. Header & Search
    assert "Lottery Companion" in content, "Must contain Lottery Companion header"
    assert "btn-search-toggle" in content, "Must contain btn-search-toggle"
    assert "search-container" in content, "Must contain search-container"
    assert "tx-search-input" in content, "Must contain tx-search-input"

    # 3. Prediction Portfolio Card
    assert "balance-card" in content, "Must contain balance-card"
    assert "portfolio-top-candidate" in content, "Must contain portfolio-top-candidate"
    assert "811767" in content, "Must display primary AI candidate 811767"
    assert "Banker" in content, "Must contain Banker hedging breakdown"
    assert "btn-pin-candidate" in content, "Must contain pin candidate button"

    # 4. Filter Segmented Control
    assert "filter-segmented-control" in content, "Must contain filter-segmented-control"
    assert "filter-all" in content, "Must contain filter-all"
    assert "filter-saved" in content, "Must contain filter-saved"
    assert "filter-checker" in content, "Must contain filter-checker"
    assert "filter-budget" in content, "Must contain filter-budget"

    # 5. Saved Tickets List & Latest Draw Verification
    assert "saved-tickets-list" in content, "Must contain saved-tickets-list container"
    assert "011781" in content, "Must display verified latest draw First Prize 011781"
    assert "48" in content, "Must display verified latest draw Last 2 Digits 48"

    # 6. Quick Action Add Button & Modal
    assert "btn-add-ticket" in content, "Must contain btn-add-ticket"
    assert "add-modal" in content, "Must contain add-modal"
    assert "input-ticket-type" in content, "Must contain input-ticket-type"
    assert "input-ticket-num" in content, "Must contain input-ticket-num"
    assert "btn-submit-transfer" in content, "Must contain btn-submit-transfer"

    # 7. iOS Bottom Tab Bar
    assert "ios-tab-bar" in content, "Must contain ios-tab-bar"
    assert "home-indicator" in content, "Must contain home-indicator"


def test_lottery_companion_interactive_scripts():
    """Verify that core interactive JavaScript handlers exist."""
    content = ROOT_WALLET.read_text(encoding="utf-8")

    assert "function escapeHtml(" in content, "Must implement escapeHtml for XSS prevention"
    assert "function renderTickets(" in content, "Must define renderTickets function"
    assert "function pinCurrentCandidate(" in content, "Must define pinCurrentCandidate function"
    assert "function saveNewTicket(" in content, "Must define saveNewTicket function"
    assert "function deleteTicket(" in content, "Must define deleteTicket function"
    assert "function setFilter(" in content, "Must define setFilter function"
    assert "function toggleSearchBar(" in content, "Must define toggleSearchBar function"
    assert "function toggleFrameMode(" in content, "Must define toggleFrameMode function"


def test_lottery_companion_security_and_accessibility():
    """Verify security escaping, non-blocking notifications, and keyboard controls."""
    content = ROOT_WALLET.read_text(encoding="utf-8")

    assert "alert(" not in content, "Must not use blocking browser alert()"
    assert "showToast(" in content, "Must use custom showToast"
    assert "Escape" in content, "Must handle Escape key for modal dismissal"
    assert "escapeHtml(t.number)" in content, "Ticket number must be escaped"
    assert "escapeHtml(t.note)" in content, "Ticket note must be escaped"
