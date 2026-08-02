# 2. Project Inventory

**Document type:** Audit report (documentation only)
**Project:** Lottery analysis suite
**Root:** `D:\xampp\htdocs\Lottery`
**Method:** Full recursive directory and file inspection (read-only). Sizes in bytes; dates omitted.

---

## 2.1 Top-Level Directory Structure

```
Lottery/
├── .agents/                    (empty)
├── .git/                       (present but unusable — see §2.8)
├── ai_engine/                  (Python: scraping, scheduling, self-learning, candidate generation)
├── analytics/                  (Python: probability, pattern, heatmap, backtest, XAI, pipeline)
├── api/                        (PHP: predict.php, debug_predict.php, run_pipeline.py, performance_api.py)
├── backend/                    (PHP: api/, config/database.php)
├── dashboard/                  (HTML/JS: manager.html, performance.html, strategy.html, app.js)
├── database/                   (CSV datasets, schema.sql, predictions/, backtest/, api/, simulation/)
├── ensemble_model/             (Python: predictor.py)
├── frontend/                   (empty: src/, public/)
├── i18n/                       (empty: en.json, th.json — 0 bytes)
├── reports/                    (summary_report.md, audit/ — this set)
├── trend_scanner/              (Python: trend_scanner.py)
└── performance.json            (root-level metrics artifact)
```

## 2.2 Empty Directories (11)

| Path |
|---|
| `ai_engine/ensemble_model/` |
| `ai_engine/pattern_engine/` |
| `ai_engine/simulation_engine/` |
| `analytics/strategy_engine/` |
| `analytics/trend_scanner/` |
| `database/predictions/` *(empty at audit time — see §2.7)* |
| `dashboard/charts/` |
| `dashboard/components/` |
| `frontend/src/` |
| `frontend/public/` |
| `.agents/` |

## 2.3 Zero-Byte Files (6)

| File | Note |
|---|---|
| `backend/api/history.php` | Declared API action is empty |
| `backend/api/statistics.php` | Declared API action is empty |
| `database/api/history.php` | Empty |
| `database/api/statistics.php` | Empty |
| `i18n/en.json` | Localization empty |
| `i18n/th.json` | Localization empty |

## 2.4 Python Modules (by directory)

### `ai_engine/`
| File | Size (bytes) | Purpose |
|---|---|---|
| `self_learning.py` | 20,309 | Per-run evaluation, weight adaptation, logging to `prediction_log.json` |
| `self_learning_manager.py` | 24,948 | Orchestrates evaluation, baseline comparison, weight persistence to `ensemble_weights.json` |
| `scrapers/expand_history.py` | 13,619 | History expansion via web sources |
| `scrapers/lottery_scraper.py` | 17,426 | Lottery scraping; defines `parse_thairath_page` **twice** (line 190 and line 403) |
| `scrapers/update_scheduler.py` | 18,139 | Scheduled scrape + feature/temporal rebuild; hardcoded DB credentials (lines 65–70) |
| `scrapers/updater.log` | 585 | 7-line log dated 2026-03-12 (only log artifact) |
| `generator/candidate_generator.py` | 2,370 | Orphaned; reads stale `database/dataset/lottery_temporal_features.csv`; no callers |

### `analytics/`
| File | Size (bytes) | Purpose |
|---|---|---|
| `backtest_engine.py` | 6,606 | Backtest; random placeholder predictions (§5.2) |
| `explainable_ai.py` | 21,107 | Per-position Thai/English explanations; recomputes factors instead of reading model attribution |
| `feature_engineering.py` | 3,750 | Builds `lottery_features.csv` |
| `heatmap_engine.py` | 12,030 | Heatmap analysis |
| `model_adjustments.json` | 25,590 | 5 adjustment records; last `2026-03-14`, `model_score: 40.0` |
| `monte_carlo_engine.py` | 5,889 | Monte Carlo simulation |
| `pattern_engine.py` | 26,896 | Pattern analysis |
| `performance_analyzer.py` | 14,444 | Analyzes `prediction_history.csv` → `accuracy_report.json` |
| `predict_pipeline.py` | 5,104 | Pipeline runner; "pattern" step is non-functional (returns last 5 draws) |
| `prediction_history.py` | 13,636 | Logs predictions + actuals to `prediction_history.json/csv` |
| `probability_advanced.py` | 17,674 | Advanced probability features |
| `probability_engine.py` | 20,010 | Base probability engine |
| `result_fetcher.py` | 12,161 | Fetches draw results; regex-based extraction |
| `strategy_optimizer.py` | 3,124 | Strategy optimization |
| `temporal_weight_engine.py` | 1,696 | Temporal feature weighting |

### `ensemble_model/`
| File | Size (bytes) | Purpose |
|---|---|---|
| `predictor.py` | ~13,900 | Ensemble predictor; hardcoded `WEIGHTS` (line 51), reversed transition matrix (§6.4) |

### `trend_scanner/`
| File | Size (bytes) | Purpose |
|---|---|---|
| `trend_scanner.py` | ~8,000 | Streak/spike/surge detection; reporting only — not wired into ensemble |

### `api/` (mixed)
| File | Size (bytes) | Purpose |
|---|---|---|
| `run_pipeline.py` | — | CLI pipeline runner |
| `debug_predict.php` | 1,641 | Debug helper |
| `performance_api.py` | 42 | Placeholder (single line / no logic) |
| `predict.php` | — | PHP API (duplicates `backend/api/predict.php`) |

## 2.5 PHP Modules

| File | Size (bytes) | Purpose / Status |
|---|---|---|
| `backend/config/database.php` | ~200 | MySQL credentials, hardcoded `localhost / root / "" / lottery_ai` |
| `backend/api/predict.php` | ~4,600 | Full API: predict, history, analytics, run_pipeline, fetch_result; uses `shell_exec` |
| `backend/api/history.php` | 0 | **Empty** |
| `backend/api/statistics.php` | 0 | **Empty** |
| `api/predict.php` | — | Near-duplicate of `backend/api/predict.php`; CORS `*` at line 7 |
| `api/debug_predict.php` | 1,641 | Debug helper |
| `database/api/predict.php` | ~2,700 | Broken: includes `../config/database.php` which does not exist (`database/config/` absent) |
| `database/api/history.php` | 0 | **Empty** |
| `database/api/statistics.php` | 0 | **Empty** |

## 2.6 Frontend / Dashboard

| File | Size (bytes) | Purpose |
|---|---|---|
| `dashboard/app.js` | 7,451 | Dashboard logic; uses `/Lottery/api/predict.php` (line 1); unescaped `innerHTML` (lines 71–83); assumes `pos.reasons.slice(0,2)` shape (line 149) that does not match cache |
| `dashboard/manager.html` | 35,642 | Manager dashboard; uses `../backend/api/predict.php` (line 493); unescaped candidate rendering (lines 592–600) |
| `dashboard/performance.html` | 19,904 | Performance dashboard; first fetches nonexistent `../analytics/performance.json`, falls back to root `performance.json` |
| `dashboard/strategy.html` | 37,306 | Strategy dashboard; fetches `../api/predict.php`, `../analytics/performance.json`, `../database/predictions/pipeline_cache.json` |

## 2.7 Data Artifacts (`database/`)

| Artifact | Content / State |
|---|---|
| `schema.sql` | Defines `lottery_results` and `predictions` tables |
| `dataset/lottery_history.csv` | **467 rows**, `2006-12-30` → `2026-07-01`, descending order; `2026-04-01 → 292514` |
| `dataset/lottery_features.csv` | **459 rows**, latest `2026-03-01` (stale) |
| `dataset/lottery_temporal_features.csv` | **459 rows**, latest `2026-03-01` (stale) |
| `predictions/prediction_history.json` | 2 entries targeting `2026-04-01` with `actual_result: "123456"` (fabricated) |
| `predictions/prediction_history.csv` | Mirrors the fabricated `123456` |
| `predictions/prediction_log.json` | Second, divergent prediction log |
| `predictions/accuracy_report.json` | Derived from fabricated data |
| `predictions/ensemble_weights.json` | 8 weights: positional_freq 0.2, rolling_heat 0.2, conditional 0.15, transition 0.1, pair_lift 0.1, pattern_hot 0.1, gap_overdue 0.08, temporal_trend 0.07 — **never read by predictor** |
| `predictions/pipeline_cache.json` | 1,272 lines; schema `status/candidates(number,score,digits,confidence)/position_scores/...` |
| `predictions/pipeline_output.json` | Different schema (`top_predictions: number/confidence/votes`); orphaned output |
| `backtest/backtest_report.json` | 359 draws; 0 exact matches; `avg_digit_hits 2.29`; `accuracy_score 3766.67` (invalid) |
| `simulation/monte_carlo_results.json` | 100,000 simulations, 459 draws |

### `performance.json` (root)
```json
{ "updated": "2026-07-03T00:50:34.652011", "evaluated": 2,
  "avg_positional_hits": 0.0, "avg_digit_hits": 4.0, "exact_matches": 0 }
```
Derived from the fabricated `123456` records (§2.7).

## 2.8 Version Control

- `.git/` directory exists (`Test-Path .git` → `True`).
- `git log` and `git status` both return `fatal: not a git repository`.
- **Conclusion:** repository metadata is incomplete/corrupt. Commit history and authorship cannot be verified. (See also `reports/audit/09-gap-analysis.md` §9.8.)

## 2.9 Runtime Environment (observed)

| Item | Value |
|---|---|
| Python | 3.12.10 |
| Installed packages | numpy 2.4.3, pandas 3.0.1, scikit-learn 1.8.0, scipy 1.17.1, beautifulsoup4 4.14.3, mysql-connector-python 9.6.0, PyMySQL 1.1.2, requests 2.32.5, schedule 1.2.2 |
| ML libraries installed but **never imported** | numpy, pandas, scikit-learn, scipy (grep: "No files found") |
| No `requirements.txt` or `Pipfile` | not reproducible from source |

## 2.10 Inventory Summary

| Metric | Count |
|---|---|
| Python source files (non-empty) | ~30 |
| PHP files | 9 (5 empty) |
| HTML/JS dashboard files | 4 |
| JSON/CSV/log artifacts | 17+ |
| Test files | 0 |
| Empty directories | 11 |
| Zero-byte files | 6 |
