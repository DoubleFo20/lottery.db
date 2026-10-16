# TASKS.md — Mission-Critical Workplan & Progress

**Feature Branch:** `feat/mission-critical-remediation`  
**Status:** Verification & Ready for Review  
**Lead Orchestrator:** ARGON

---

## Phase 0: Safety, Audit & Baseline
- [x] Run baseline test suite (`pytest tests/`) — 222 passed.
- [x] Create feature branch `feat/mission-critical-remediation`.
- [x] Verify existing fixes (`load_ensemble_weights`, transition matrix, fabricated actuals).
- [x] Document root cause of hardcoded 64 in `manager.html` and stale data in `index.html`.

## Phase 1: Data & Core Correctness
- [x] Regenerate `lottery_features.csv` and `lottery_temporal_features.csv` to 473 rows (including latest draw 2026-10-16).
- [x] Update `api/run_pipeline.py:read_dataset_summary()` to include `last2`, `front3`, and `back3`.
- [x] Deduplicate `prediction_history.json` (remove duplicate 2026-04-01 entry).
- [x] Re-run `analytics/performance_analyzer.py --save performance.json` to reflect deduplicated reality (evaluated: 2).
- [x] Update `manager.html` & `dashboard/manager.html` to dynamically render `last2`, `front3`, `back3` from `meta.dataset` and remove hardcoded 64/730640 fallbacks (verified 2026-10-16: 011781, 48).
- [x] Update `index.html`, `strategy.html`, `dashboard/strategy.html`, `dashboard/index.html` fallback dataset and default UI values to 2026-10-16 (011781, 48, 402/392, 171/255).

## Phase 2: Prediction Model Evaluation
- [x] Extend `analytics/backtest_engine.py` to evaluate 6-digit, last-2, and 3-digit metrics separately.
- [x] Calibrate confidence labels (distinguish relative score rank vs. true outcome probability).
- [x] Run comparative walk-forward backtest against empirical random baseline (`database/backtest/comparative_report.json`).

## Phase 3: Premium UI/UX & Quality
- [x] Refactor `dashboard/app.js` with XSS sanitization (`escapeHtml`), multi-path API resilience, and XAI reasons object support (`{th, en}`).
- [x] Fix unescaped `innerHTML` and XSS vectors in dashboard controllers.
- [x] Fix broken Thai character encodings (`หน้า 3`, `ท้าย 3`).
- [x] Populate `i18n/th.json` and `i18n/en.json` with comprehensive bilingual dictionaries.

## Phase 4: Optimization & Code Quality
- [x] Delete 4 zero-byte dead placeholder files (`backend/api/history.php`, `backend/api/statistics.php`, `database/api/history.php`, `database/api/statistics.php`).
- [x] Replace broken `database/api/predict.php` with clean forwarding shim to canonical `api/predict.php`.
- [x] Add unit test suite `tests/test_data_integrity_and_backtest.py` covering ground truth, deduplication, backtest metrics, and dashboard parity.
- [x] Rebuild 3D assets (`npm run build`).

## Phase 5: Verification & Release
- [x] Full regression test suite passing: **229 / 229 passed**.
- [x] Verify identical ground truth across all dashboards (`index.html`, `strategy.html`, `manager.html`, `performance.html`, `3d.html`).
