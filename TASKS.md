# TASKS.md — Mission-Critical Workplan & Progress

**Feature Branch:** `feat/mission-critical-remediation`  
**Status:** In Progress (Paused on request)

---

## Phase 0: Safety, Audit & Baseline
- [x] Run baseline test suite (`pytest tests/`) — 222 passed.
- [x] Create feature branch `feat/mission-critical-remediation`.
- [x] Verify existing fixes (`load_ensemble_weights`, transition matrix, fabricated actuals).
- [x] Document root cause of hardcoded 64 in `manager.html` and stale data in `index.html`.

## Phase 1: Data & Core Correctness
- [x] Regenerate `lottery_features.csv` and `lottery_temporal_features.csv` to 472 rows.
- [ ] Update `api/run_pipeline.py:read_dataset_summary()` to include `last2`, `front3`, and `back3`.
- [ ] Deduplicate `prediction_history.json` (remove duplicate 2026-04-01 entry).
- [ ] Re-run `analytics/performance_analyzer.py --save performance.json` to reflect deduplicated reality.
- [ ] Update `manager.html` to dynamically render `last2`, `front3`, `back3` from `meta.dataset` and remove hardcoded 64/730640 fallbacks.
- [ ] Update `index.html` and `strategy.html` fallback dataset and default UI values to 2026-10-01.

## Phase 2: Prediction Model Evaluation
- [ ] Extend `analytics/backtest_engine.py` to evaluate 6-digit, last-2, and 3-digit metrics separately.
- [ ] Calibrate confidence labels (distinguish relative score rank vs. true outcome probability).
- [ ] Run comparative walk-forward backtest against empirical random baseline.

## Phase 3: Premium UI/UX
- [ ] Professional fintech styling for `manager.html` and `strategy.html`.
- [ ] Fix unescaped `innerHTML` and XSS vectors, preferring `textContent`.
- [ ] Fix broken Thai character encodings (`˹ 3` -> `หน้า 3`, etc.).
- [ ] Unify API base paths across all dashboards.

## Phase 4: Optimization & Code Quality
- [ ] Consolidate duplicate `index.html` and `strategy.html` or establish single source of truth.
- [ ] Add unit tests for `read_dataset_summary()`, deduplication, and backtest metrics.

## Phase 5: Verification & Release
- [ ] Full regression test suite passing.
- [ ] Verify identical ground truth across all 4 dashboards (`index.html`, `strategy.html`, `manager.html`, `performance.html`).
