"""tests/test_mobile_wallet.py
Comprehensive verification test suite for the High-Fidelity Mobile App UI (mobile-wallet.html):
- DOM elements verification (Dynamic Island, Status bar, Balance Card, Filter Pills, Transactions, Quick Transfer, Bottom Tabs)
- SHA-256 byte-for-byte parity between root mobile-wallet.html and dashboard/mobile-wallet.html
- Interactive filter logic, currency toggle logic, and quick transfer modal script checks
- iOS glassmorphism styling, design tokens, and XSS sanitization verification
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


def test_mobile_wallet_dom_elements():
    """Verify that mobile-wallet.html contains all essential iOS banking DOM structures."""
    content = ROOT_WALLET.read_text(encoding="utf-8")

    # 1. Dynamic Island & iOS Status Bar Notch
    assert "ios-status-bar" in content, "Must contain ios-status-bar"
    assert "status-clock" in content, "Must contain status-clock"
    assert "dynamic-island" in content, "Must contain dynamic-island"
    assert "status-icons" in content, "Must contain status-icons"
    assert "battery-pill" in content, "Must contain battery-pill"

    # 2. Header & Search
    assert "Transaction History" in content, "Must contain Transaction History header"
    assert "btn-search-toggle" in content, "Must contain btn-search-toggle"
    assert "search-container" in content, "Must contain search-container"
    assert "tx-search-input" in content, "Must contain tx-search-input"

    # 3. Glassmorphic Current Balance Card
    assert "current-balance-card" in content, "Must contain current-balance-card"
    assert "Current Balance" in content, "Must contain Current Balance label"
    assert "€12,480.75" in content or "12,480.75" in content, "Must display initial balance €12,480.75"
    assert "currency-pill-toggle" in content, "Must contain currency toggle pills"
    assert "Manage Accounts" in content, "Must contain Manage Accounts link"

    # 4. Segmented Control Filter Pills
    assert "filter-segmented-control" in content, "Must contain segmented control container"
    assert "filter-all" in content, "Must contain filter-all button"
    assert "filter-income" in content, "Must contain filter-income button"
    assert "filter-expenses" in content, "Must contain filter-expenses button"

    # 5. Filterable Transaction History List Items
    assert "group-today" in content, "Must contain Today transaction group"
    assert "Spotify" in content, "Must contain Spotify transaction"
    assert "10.99" in content, "Must contain €10.99 amount"
    assert "Transfer from Alice" in content, "Must contain Transfer from Alice transaction"
    assert "150.00" in content, "Must contain €150.00 amount"
    assert "Grocery" in content, "Must contain Grocery transaction"
    assert "64.50" in content, "Must contain €64.50 amount"

    assert "group-yesterday" in content, "Must contain Yesterday transaction group"
    assert "Salary" in content, "Must contain Salary transaction"
    assert "3,850.00" in content or "3850" in content, "Must contain Salary amount"
    assert "Dinner" in content, "Must contain Dinner transaction"
    assert "88.30" in content, "Must contain Dinner amount"

    # 6. Floating Frosted Quick Transfer Button
    assert "quick-transfer-btn" in content, "Must contain quick-transfer-btn"
    assert "Quick Transfer" in content, "Must contain Quick Transfer label"
    assert "+ Send Money" in content or "Send Money" in content, "Must contain Send Money button text"

    # 7. iOS Bottom Navigation Tab Bar & Home Indicator
    assert "ios-tab-bar" in content, "Must contain ios-tab-bar"
    assert "Home" in content, "Must contain Home tab"
    assert "Accounts" in content, "Must contain Accounts tab"
    assert "Send" in content, "Must contain Send tab"
    assert "Pay" in content, "Must contain Pay tab"
    assert "More" in content, "Must contain More tab"
    assert "home-indicator" in content, "Must contain iOS home indicator"

    # 8. Interactive Quick Transfer Modal / Bottom Sheet
    assert "transfer-modal" in content, "Must contain transfer-modal"
    assert "bottom-sheet" in content, "Must contain bottom-sheet"
    assert "Recent Contacts" in content, "Must contain Recent Contacts section"
    assert "Alice" in content, "Must contain contact Alice"
    assert "Bob" in content, "Must contain contact Bob"
    assert "Charlie" in content, "Must contain contact Charlie"
    assert "NovaTech" in content, "Must contain contact NovaTech"
    assert "transfer-amount-input" in content, "Must contain transfer amount input"
    assert "btn-submit-transfer" in content, "Must contain confirm transfer button"


def test_mobile_wallet_interactive_script():
    """Verify that all core interactive JavaScript handlers and state controllers exist."""
    content = ROOT_WALLET.read_text(encoding="utf-8")

    # Script logic presence
    assert "function toggleCurrency(" in content, "Must define toggleCurrency function"
    assert "function setFilter(" in content, "Must define setFilter function"
    assert "function filterTransactions(" in content, "Must define filterTransactions function"
    assert "function openTransferModal(" in content, "Must define openTransferModal function"
    assert "function closeTransferModal(" in content, "Must define closeTransferModal function"
    assert "function executeTransfer(" in content, "Must define executeTransfer function"
    assert "function toggleSearchBar(" in content, "Must define toggleSearchBar function"
    assert "function toggleFrameMode(" in content, "Must define toggleFrameMode function"
    assert "EUR_TO_THB_RATE" in content, "Must define EUR to THB exchange rate"


def test_mobile_wallet_styling_and_tokens():
    """Verify that iOS light mode glassmorphism styling and pastel accents are present."""
    content = ROOT_WALLET.read_text(encoding="utf-8")

    # Colors and glassmorphism tokens
    assert "backdrop-filter" in content, "Must use backdrop-filter for glassmorphism"
    assert "#38bdf8" in content, "Must contain pastel blue accent (#38bdf8)"
    assert "#a855f7" in content, "Must contain soft purple accent (#a855f7)"
    assert "Inter" in content, "Must include Inter font"
    assert "full-width-mode" in content, "Must support full-width mode toggle"


def test_mobile_wallet_security_and_sanitization():
    """Verify that user inputs in transfer note and contacts are sanitized before DOM insertion (Coding Standards D15)."""
    content = ROOT_WALLET.read_text(encoding="utf-8")

    assert "escapeHtml" in content, "Must implement escapeHtml function to prevent XSS"
    assert "escapeHtml(selectedContactName)" in content, "Contact name must be sanitized"
    assert "escapeHtml(noteInput?.value" in content, "Note input must be sanitized"


def test_mobile_wallet_dynamic_interaction_fixes():
    """Verify that interaction edge cases, validation, and dynamic element binding are properly implemented."""
    content = ROOT_WALLET.read_text(encoding="utf-8")

    # 1. viewTxDetail called with this for dynamic currency extraction
    assert 'onclick="viewTxDetail(this)"' in content, "Transaction rows must use dynamic element binding for detail view"
    assert "target.querySelector('.tx-title')" in content, "viewTxDetail must extract title dynamically"
    assert "target.querySelector('.tx-amount')" in content, "viewTxDetail must extract amount dynamically"

    # 2. No blocking browser alert() calls in executeTransfer
    assert "alert(" not in content, "Must not use blocking browser alert() in mobile app mockup"
    assert "showToast(" in content, "Must use custom showToast for feedback"
    assert "input-error" in content, "Must trigger input-error animation on validation failure"

    # 3. Note reset and amount input reset in openTransferModal & executeTransfer
    assert "noteInput.value = ''" in content, "Must clear note input on modal reset and after transfer"

    # 4. Filter matches query across both merchant name and row text (amounts/subtitles)
    assert "rowText.includes(query)" in content, "Filter must match transaction text including amounts"
    assert ".filter(r => r.style.display !== 'none')" in content, "Group visibility must check actual display property"

    # 5. Quick chips support incrementing
    assert "cur + val" in content, "Quick amount chips should increment when amount is already present"


def test_mobile_wallet_visual_fidelity_and_gestures():
    """Verify iOS visual fidelity details, mockup parity, and mobile gestures."""
    content = ROOT_WALLET.read_text(encoding="utf-8")

    # 1. Segmented control divider lines
    assert ".filter-pill-btn:not(:last-child):not(.active)::after" in content, "Must include iOS segmented control divider lines"

    # 2. Mockup side peek glow accents flanking balance card
    assert "balance-card-wrapper" in content, "Must contain balance card wrapper"
    assert "card-side-peek peek-left" in content, "Must contain left side peek accent"
    assert "card-side-peek peek-right" in content, "Must contain right side peek accent"

    # 3. Dynamic island spring transform transition
    assert "transform 0.25s cubic-bezier" in content, "Dynamic Island notch must feature smooth spring transform transition"

    # 4. Mobile touch gestures & accessibility
    assert "Escape" in content, "Must support Escape key dismissal for transfer modal"
    assert "touchmove" in content or "touchstart" in content, "Must support swipe gestures for modal dismissal"
    assert "toast-notification error" in content or ".toast-notification.error" in content, "Must support error state toast styling"

