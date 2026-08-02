# 3. Architecture Audit

**Document type:** Audit report (documentation only)
**Project:** Lottery analysis suite
**Root:** `D:\xampp\htdocs\Lottery`

---

## 3.1 Intended Architecture (from code structure)

The project is organized around the following conceptual layers:

1. **Data layer:** CSV datasets under `database/dataset/`, JSON artifacts under `database/predictions/`, MySQL schema (`database/schema.sql`).
2. **Scraping / data pipeline:** `ai_engine/scrapers/` (lottery_scraper.py, expand_history.py, update_scheduler.py).
3. **Analytics engines:** `analytics/` (probability, pattern, heatmap, monte carlo, feature engineering, backtest, XAI).
4. **Ensemble prediction:** `ensemble_model/predictor.py`.
5. **Self-learning / adaptation:** `ai_engine/self_learning.py`, `ai_engine/self_learning_manager.py`.
6. **Trend reporting:** `trend_scanner/trend_scanner.py`.
7. **API / orchestration:** `api/predict.php` and `backend/api/predict.php` (PHP) invoking Python via `shell_exec`; `api/run_pipeline.py`.
8. **Presentation:** `dashboard/` (manager, performance, strategy) and empty `frontend/`.

## 3.2 Architectural Scores

| Index | Score | Rationale |
|---|---|---|
| Architecture | **35 / 100** | No abstraction between layers; CSV coupled directly into business logic; duplicate API layers; phantom empty directories |
| Scalability | **30 / 100** | CSV-file storage; full pipeline + CSV re-read per request; PHP `shell_exec` Python process startup per request; MySQL schema unused for reads |

## 3.3 Layer-Boundary Violations (evidence)

1. **CSV coupling everywhere.** Signal extractors in `ensemble_model/predictor.py` open `database/dataset/lottery_history.csv` directly. Feature files are read by `analytics/feature_engineering.py`, `analytics/temporal_weight_engine.py`, and `ai_engine/generator/candidate_generator.py`. There is no data-access abstraction or repository layer.
2. **Business logic embedded in dashboards.** `dashboard/manager.html` embeds a TH/EN localization replacement script and prediction-rendering logic directly in HTML, rather than in `dashboard/app.js`.
3. **PHP shells out to Python.** `api/predict.php` (line 28) and `backend/api/predict.php` (line 66) use `shell_exec('python …')` to run pipelines on demand. This couples the web layer to a local Python runtime and blocks under concurrency.
4. **Two API layers.** `api/predict.php` and `backend/api/predict.php` are near-duplicates. Consumers disagree: `dashboard/app.js:1` calls `/Lottery/api/predict.php`, `dashboard/manager.html:493` calls `../backend/api/predict.php`, and `dashboard/strategy.html` calls `../api/predict.php`. This is a versioning hazard (fixing one leaves the other stale).
5. **Orphaned output.** `database/predictions/pipeline_output.json` uses a schema (`top_predictions: number/confidence/votes`) that does not match `pipeline_cache.json` (`candidates: number/score/digits/confidence`) produced by `analytics/predict_pipeline.py`.
6. **Phantom structure.** 11 empty directories (see `reports/audit/02-project-inventory.md` §2.2) imply module boundaries that do not exist, misrepresenting progress and complicating onboarding.

## 3.4 Data-Flow Analysis

### 3.4.1 The self-learning loop (broken)
```
scrape → lottery_history.csv
        → feature_engineering.py → lottery_features.csv
        → temporal_weight_engine.py → lottery_temporal_features.csv
        → predictor.py (hardcoded WEIGHTS, line 51)
        → prediction_history.py → prediction_history.json  ("actual_result": "123456" — fabricated)
        → performance_analyzer.py → accuracy_report.json
        → self_learning.py → prediction_log.json
        → self_learning_manager.py → ensemble_weights.json   [WRITTEN]
        → (predictor.py) ...                               [NEVER READ — loop broken here]
```
**Critical gap:** `ensemble_weights.json` is written but never consumed. Verified by grep: only `self_learning.py`, `self_learning_manager.py`, `run_pipeline.py:67`, and `explainable_ai.py` reference it — never the predictor. See `reports/audit/06-ai-audit.md` §6.2.

### 3.4.2 The pipeline (functional but data-inconsistent)
```
api/predict.php (shell_exec) → run_pipeline.py → analytics/predict_pipeline.py
  → probability_engine, probability_advanced, pattern_engine, heatmap_engine,
    monte_carlo_engine, temporal_weight_engine, trend_scanner, explainable_ai
  → pipeline_cache.json (1,272 lines; candidates + position_scores)
  → dashboard reads cache
```
**Defects in the flow:**
- `predict_pipeline.py:62` "pattern" step is a non-functional set comprehension that returns the last 5 draws as candidates.
- Feature/temporal CSVs are stale by 8 draws (`2026-03-01` vs history to `2026-07-01`), so any module reading them (e.g., `candidate_generator.py`) operates on outdated input.
- `performance.json` and `accuracy_report.json` derive from fabricated `"123456"` actuals.

### 3.4.3 Result verification (fragmented)
- Actuals can come from `result_fetcher.py` (regex extraction), `lottery_scraper.py` (two `parse_thairath_page` definitions), or `update_scheduler.py` (duplicate parser, lines 165–293). No single verification path.

## 3.5 Data Integrity Evidence

| Item | Evidence | Impact |
|---|---|---|
| Master history | 467 rows, `2006-12-30` → `2026-07-01`, desc | Ground truth (trusted) |
| Feature/temporal CSVs | 459 rows, latest `2026-03-01` | Stale; consumers missing 8 draws |
| `prediction_history.json` | `actual_result: "123456"` for `2026-04-01` | Real result is `292514` (CSV row 8) — fabricated metric source |
| Root `performance.json` | `evaluated: 2, avg_digit_hits: 4.0` | Derived from fabricated actuals |
| `analytics/model_adjustments.json` | 5 entries; last `2026-03-14`; `model_score: 40.0` | Derived from fabricated actuals; source of "Grade C" |
| `reports/summary_report.md` | dated `2026-03-12`; "459 งวด"; "Grade C (40/100)" | Stale and based on non-functional backtest/fabricated data |

## 3.6 Concurrency & Scalability Concerns

1. **Blocking pipeline execution.** Every dashboard refresh can trigger `shell_exec` of a full Python pipeline (multi-second Python startup + full CSV re-read). No caching beyond the JSON artifacts; no request queue.
2. **Process-per-request model.** No long-running service or worker. Each API call may spawn Python processes.
3. **CSV as primary store.** The MySQL schema (`database/schema.sql`) is essentially unused for reads; no read path into the `predictions` table was found. CSV-file concurrency is unprotected.
4. **Scheduler coupling.** `update_scheduler.py` mixes scrape scheduling, DB writes, feature rebuild, and error handling in one module with hardcoded credentials (lines 65–70).

## 3.7 Architectural Risks

| Risk | Level | Reason |
|---|---|---|
| PHP↔Python `shell_exec` coupling | High | Blocks, non-portable, fails under load |
| Phantom module structure | High | Misleading progress; empty dirs imply features that do not exist |
| No data-access abstraction | High | Any schema/storage change touches every engine |
| Duplicate API layers | High | Fix drift: one layer updated, the other stale |
| MySQL unused for reads | Medium | DB investment has no consumer; CSV remains source of truth |
| Self-learning broken loop | Critical | The system's signature feature does nothing (see `06-ai-audit.md`) |

## 3.8 Architecture Recommendations (documentation only)

1. Introduce a single data-access layer (repository) for `lottery_history.csv` and prediction artifacts.
2. Consolidate to one API layer; standardize the dashboard to a single API base URL.
3. Replace `shell_exec` with a persistent Python service or a scheduled worker that writes caches (dashboard reads caches only).
4. Unify the prediction-log format and the pipeline-cache schema; delete `pipeline_output.json`.
5. Wire `ensemble_weights.json` consumption into the predictor (see roadmap).
6. Remove empty directories and zero-byte files, or implement their declared purpose.

**Cross-references:** `04-backend-audit.md`, `05-analytics-audit.md`, `06-ai-audit.md`, `09-gap-analysis.md`.
