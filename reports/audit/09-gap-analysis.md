# 9. Gap Analysis

**Document type:** Audit report (documentation only)
**Project:** Lottery analysis suite
**Root:** `D:\xampp\htdocs\Lottery`

Purpose: compare the project's intended capability (per its structure, dashboards, and artifact names) against what actually works, with evidence for every gap.

---

## 9.1 Gap Summary Table

| # | Intended capability | Actual state | Evidence | Gap type |
|---|---|---|---|---|
| G1 | Self-learning / adaptive weights | Non-functional end-to-end | `ensemble_weights.json` never read by predictor (`ensemble_model/predictor.py:51` hardcoded `WEIGHTS`) | Functional gap (critical) |
| G2 | Backtest model evaluation | Random baseline + invalid formula | `analytics/backtest_engine.py:79-82, 138`; `backtest_report.json` `accuracy_score: 3766.67` | Functional gap (critical) |
| G3 | Accurate performance metrics | Metrics derived from fabricated actuals | `prediction_history.json` `"123456"` vs real `292514` (`lottery_history.csv`) | Data-integrity gap (critical) |
| G4 | Up-to-date feature datasets | Stale by 8 draws | features/temporal = 459 rows (max `2026-03-01`) vs history = 467 (max `2026-07-01`) | Data-integrity gap (critical) |
| G5 | Correct transition probabilities | Direction reversed | `predictor.py:123-138` on descending rows | Correctness gap (critical) |
| G6 | Calibrated confidence | Uncalibrated relative rank | top candidate `confidence: 100.0` in cache | Quality gap |
| G7 | Model-true explanations | Re-computed approximations | `explainable_ai.py:44-49` own `FACTOR_WEIGHTS` | Quality gap |
| G8 | Pattern signal in pipeline | Non-functional step | `predict_pipeline.py:62` returns last 5 draws | Functional gap |
| G9 | Trend scanner integration | Reporting only, not a signal | scanner output in cache `analytics`, not consumed by predictor | Integration gap |
| G10 | Single prediction log | Two divergent logs | `prediction_history.json` vs `prediction_log.json` | Consistency gap |
| G11 | Single API layer | Two near-duplicate layers | `api/predict.php` vs `backend/api/predict.php`; 3 dashboard paths | Architecture gap |
| G12 | Working history/statistics endpoints | Empty PHP files | `backend/api/history.php`, `statistics.php` (0 bytes) | Functional gap |
| G13 | Working `database/api/` router | Broken include | missing `database/config/database.php` | Functional gap |
| G14 | MySQL as data layer | Write-only; no read consumer | no module reads `predictions` table | Architecture gap |
| G15 | Localization (EN/TH) | Empty i18n; ad-hoc script in `manager.html` | `i18n/en.json`, `th.json` (0 bytes) | Functional gap |
| G16 | Modern frontend | Empty scaffolding | `frontend/src`, `frontend/public` empty | Functional gap (0%) |
| G17 | Tests | None | glob: no `test_*.py`, no `*_test.py` | Quality gap |
| G18 | ML capability | No ML used despite installed libs | grep: no ML-library imports | Capability gap (per code), latent infra present |
| G19 | Reproducible environment | No `requirements.txt`/README | none present | Process gap |
| G20 | Version control | Repo metadata unusable | `.git` present but `git` → `fatal: not a git repository` | Process gap |

## 9.2 Capability Coverage by Area

| Area | % of declared capability actually working |
|---|---|
| Data collection / scraping | ~60% (parser duplication, only one stale log artifact `updater.log`) |
| Analytics engines | ~85% (individual engines sound; backtest & pipeline-step broken) |
| Prediction / ensemble | ~70% (functions, but reversed transition, uncalibrated, orphaned helpers) |
| Self-learning | **0%** (weights never consumed) |
| API / backend | ~50% (2 empty endpoints, 1 broken router, 1 missing metrics file) |
| Dashboard | ~70% (renders, but XAI mismatch, missing metrics file, XSS) |
| Frontend (modern) | 0% |
| i18n | 0% |
| Testing | 0% |
| Production readiness | ~20% |

## 9.3 Data-State Gaps (verified)

| Data artifact | Has | Should have | Missing |
|---|---|---|---|
| `lottery_history.csv` | 467 draws (to `2026-07-01`) | ground truth | — (OK) |
| `lottery_features.csv` | 459 (to `2026-03-01`) | 467 | 8 draws |
| `lottery_temporal_features.csv` | 459 (to `2026-03-01`) | 467 | 8 draws |
| `prediction_history.json` | 2 entries, `actual_result` `"123456"` | real results | real actuals |
| `performance.json` (root) | `evaluated: 2, avg_digit_hits: 4.0` | derived from real actuals | real basis |
| `backtest_report.json` | 359 draws, `accuracy 3766.67` | model-based, correct formula | real predictions |
| `analytics/performance.json` | **absent** | present (dashboard expects it) | the file itself |
| `ensemble_weights.json` | 8 weights | consumed by predictor | consumption path |

## 9.4 Gap Severity Matrix

| Severity | Gaps |
|---|---|
| Critical | G1, G2, G3, G4, G5 |
| High | G8, G9, G11, G12, G13, G14, G16 |
| Medium | G6, G7, G10, G15, G17, G18 |
| Low | G19, G20 |

## 9.5 Items with Insufficient Evidence (documented per audit rules)

| Item | Why it cannot be confirmed |
|---|---|
| Origin of `actual_result: "123456"` (manual entry vs. code bug) | No provenance in repository; history-log mechanism allows both |
| Why feature pipeline stopped at `2026-03-01` | Scheduler trigger exists (`update_scheduler.py:382-396`); no logs beyond `updater.log` (7 lines, 2026-03-12) to diagnose |
| MySQL table contents | Not visible from filesystem; no read consumer to observe |
| Live scraper behavior | Only one old log artifact; no current run logs |
| Git history | `.git` unusable — no commit data |
| Live API behavior under browser access | Requires a running server; audit was static |

## 9.6 Gap-Closure Priorities

1. **Data integrity first:** G3, G4 (correct actuals; regenerate feature datasets).
2. **Core correctness:** G1, G2, G5, G8 (wire weights, real backtest, fix matrix, fix pattern step).
3. **Consolidation:** G10, G11, G12, G13, G15, G16 (single log/API, delete dead files, real i18n, decide on frontend).
4. **Quality & ML:** G6, G7, G9, G17, G18 (calibration, true attribution, integrate scanner, add tests, then optionally real ML).
5. **Process:** G19, G20 (requirements.txt, README, git re-init).

**Cross-references:** the ordered remediation steps are in `reports/audit/10-development-roadmap.md`; evidence details in `reports/audit/05-analytics-audit.md` and `reports/audit/06-ai-audit.md`.
