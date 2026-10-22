# TASKS.md — LOTTERY.DB Product Recovery & Premium UX V3

**Feature Branch:** `fix/lottery-product-readiness-v3`  
**Base Commit:** `e391fdb` (`origin/main`)  
**Status:** All Phases Completed & Fully Verified  
**Lead Engineering Orchestrator:** ARGON

---

## Phase 0: Repository Safety & Baseline Establishment
- [x] Fetch `origin/main` (commit `e391fdb`).
- [x] Create feature branch `fix/lottery-product-readiness-v3`.
- [x] Run baseline test suites (Python 239 passed, UI QA regression passed, Node advisory passed, Canvas stress passed).

## Phase 1: Critical Functional Repairs (P0 & P1)
- [x] **P0 — Manager Countdown & Shared Calendar Service:**
  - Removed all hardcoded draw dates (`1 ต.ค. 2569`, etc.) from HTML markups.
  - Normalized date parsing to `Asia/Bangkok` (UTC+7) in `assets/live_countdown.js`.
  - Fixed frozen `--d --h --m --s` countdown caused by synchronous script check before deferred script load.
  - Added self-healing auto-initialization across Strategy, Manager, and 3D.
  - Added unit tests in `tests/test_live_countdown.py` covering draw transitions, expired dates, and Bangkok timezone.
- [x] **P0 — 3D Showcase (`3d.html`):**
  - Softened radial vignette (expanded clear zone to 48%, reduced dark edge opacity) to eliminate pitch-black voids on wide screens.
  - Removed stale October 1 strategy content and hardcoded prediction samples (`830386`).
  - Removed misleading "100% Confidence" claim; replaced with honest heuristic rank ("Top Beam Search Candidate").
  - Dynamically bound actual AI candidate (`811767`), sum 30, 2-digit pairs, and Banker digits.
  - Added visible canvas loading spinner and fallback simulation indicator.
- [x] **P0 — Mobile Wallet -> Lottery Companion Hub (`mobile-wallet.html`):**
  - Completely purged fictional banking UI (Spotify, Alice, NovaTech salary, Euro currency, bank transfers).
  - Built Lottery Companion Hub: Saved Number Sets, Prediction Portfolio, Historical Draw Verification, and Optional Expense/Budget Logger.
  - Implemented local-first persistence via `localStorage` with XSS entity sanitization (`escapeHtml`).
  - Rewrote `tests/test_mobile_wallet.py` to assert zero fictional banking entities and verify companion features.
- [x] **P0 — AI Command Copilot (`assets/js/ai-copilot.js`):**
  - Relabeled UI as "Quick Analysis / Command Search" (ค้นหาและวิเคราะห์ข้อมูลด่วน).
  - Grounded all responses in verified dataset values (Beam Search candidates, 70/20/10 hedging allocation, 473 historical draws).
  - Eliminated fabricated variance claims ("Variance < 0.12") and fake drift assertions.
  - Zero paid AI APIs / no exposed secrets.
- [x] **P1 — Manager API Actions (`manager.html`):**
  - Added static hosting (GitHub Pages) detection for backend action triggers.
  - Handled non-JSON / 404 responses gracefully with informative guidance.
  - Never displays false success unless real backend operation succeeds.

## Phase 2: Complete Visual Redesign (Modern Premium Analytics)
- [x] **Design Tokens & System (`assets/css/premium-theme.css`):**
  - Implemented **Default Light Theme**: Background `#F5F6F4`, card surface `#FFFFFF`, text `#17212B`, primary accent `#0F766E` (Deep Teal), warm secondary `#AD8558`.
  - Implemented **Clean Dark Theme**: Charcoal slate `#12161A` / `#182026`, readable contrast, zero cyber neon glow.
  - Added persistent theme switcher (☀️ / 🌙) in top navigation bar and mobile drawer via `assets/js/nav-component.js`.
  - Applied clean typography with Thai font fallbacks and JetBrains Mono for numbers.

## Phase 3: Mirror Parity Invariant
- [x] Maintained 100% SHA-256 byte-for-byte parity across all 11 root/dashboard mirror pairs:
  - `strategy.html` <-> `index.html` <-> `dashboard/strategy.html` <-> `dashboard/index.html`
  - `manager.html` <-> `dashboard/manager.html`
  - `performance.html` <-> `dashboard/performance.html`
  - `3d.html` <-> `dashboard/3d.html`
  - `mobile-wallet.html` <-> `dashboard/mobile-wallet.html`
  - `assets/css/premium-theme.css` <-> `dashboard/assets/css/premium-theme.css`
  - `assets/live_countdown.js` <-> `dashboard/assets/live_countdown.js`
  - `assets/js/nav-component.js` <-> `dashboard/assets/js/nav-component.js`
  - `assets/js/ai-copilot.js` <-> `dashboard/assets/js/ai-copilot.js`
  - `database/predictions/hopper_3d_data.json` <-> `dashboard/hopper_3d_data.json`

## Phase 4: Full Verification & Integration
- [x] Run Python pytest suite: **240 / 240 passed (100%)**.
- [x] Run UI QA regressions test: **PASS (100% mirror parity, 0 duplicate IDs, drawer a11y)**.
- [x] Run Node advisory test: **PASS (13 / 13 passed + manager advisory browser test)**.
- [x] Run Canvas legacy stress test: **PASS (12 / 12 passed)**.
- [x] Run Next.js production build: **Clean (0 errors)**.
- [x] Capture visual QA screenshots across Desktop, Tablet, and Mobile (15 files in `reports/screenshots/`).
