# 8. Technical Debt

**Document type:** Audit report (documentation only)
**Project:** Lottery analysis suite
**Root:** `D:\xampp\htdocs\Lottery`

Scope: a categorized register of technical debt, each item with evidence and a remediation direction. No code was written and nothing was refactored.

---

## 8.1 Critical Debt

| # | Debt | Evidence | Why it matters |
|---|---|---|---|
| D1 | Self-learning → predictor weight disconnect | Weights written to `database/predictions/ensemble_weights.json`; predictor uses hardcoded `WEIGHTS` (`ensemble_model/predictor.py:51`); grep confirms the file is never read by the predictor | The advertised self-learning capability does nothing |
| D2 | Backtest uses random predictions + broken formula | `analytics/backtest_engine.py:79-82` `random.randint(0,999999)` with `# TODO`; line 138 formula yields `accuracy_score: 3766.67` in `database/backtest/backtest_report.json` | Invalidates all reported model scores (e.g., "Grade C 40/100") |
| D3 | Fabricated `actual_result` records | `database/predictions/prediction_history.json`/`.csv` record `"123456"` for `2026-04-01`; real prize in `database/dataset/lottery_history.csv` is `292514` | Poisons every downstream metric (`performance.json`, `accuracy_report.json`, `model_adjustments.json`) |
| D4 | Stale feature/temporal datasets | `lottery_features.csv` and `lottery_temporal_features.csv` = 459 rows (latest `2026-03-01`) vs 467 history rows (latest `2026-07-01`) | Consumers silently operate on data missing the last 8 draws |

## 8.2 High Debt

| # | Debt | Evidence | Why it matters |
|---|---|---|---|
| D5 | Duplicate API layers | `api/predict.php` vs `backend/api/predict.php` (near-duplicates); dashboards call three different paths (`app.js:1`, `manager.html:493`, `strategy.html`) | Version skew; fixing one layer leaves the other stale |
| D6 | Empty / broken API files | 6 zero-byte PHP files; `database/api/predict.php` includes missing `../config/database.php` (`database/config/` absent) | Endpoints promise features that do not exist; one route is broken |
| D7 | Reversed transition matrix | `ensemble_model/predictor.py:123-138` builds `rows[idx] → rows[idx+1]` on a verified descending dataset (comment at line 95); intent is `P(next_draw|current_draw)` | Core signal encodes the wrong conditional |
| D8 | Two divergent prediction logs | `prediction_history.json` (from `analytics/prediction_history.py`) vs `prediction_log.json` (from `ai_engine/self_learning.py`) | No single source of truth; evaluations disagree |
| D9 | Duplicate scraper parsers | `lottery_scraper.py` defines `parse_thairath_page` twice (line 190, line 403 — second shadows first); parsers duplicated in `update_scheduler.py:165-293` and `result_fetcher.py` | Dead code; maintenance trap; inconsistent extraction |
| D10 | Non-functional pipeline "pattern" step | `analytics/predict_pipeline.py:62` is a set comprehension returning the last 5 draws | The pattern signal is effectively absent from predictions |

## 8.3 Medium Debt

| # | Debt | Evidence | Why it matters |
|---|---|---|---|
| D11 | Uncalibrated confidence | Cache shows top candidate `confidence: 100.0`; normalized relative to top, not calibrated | Misleads users about certainty |
| D12 | XAI recomputes factors | `analytics/explainable_ai.py:44-49` applies own `FACTOR_WEIGHTS`; does not read model attribution | Explanations can diverge from actual model behavior |
| D13 | Hardcoded credentials | `backend/config/database.php` (`localhost/root/""/lottery_ai`), duplicated in `update_scheduler.py:65-70` | Security + drift risk |
| D14 | Dashboard schema mismatch | `app.js:149` expects string `reasons`; cache provides `reasons.{th,en}` | Broken explanation UI |
| D15 | Unescaped `innerHTML` | `app.js:71-83`, `manager.html:592-600` | XSS exposure |
| D16 | Shell-exec architecture | `api/predict.php:28`, `backend/api/predict.php:66` | Blocks; non-portable; fails under concurrency |
| D17 | Open CORS / no auth | `Access-Control-Allow-Origin: *` (both APIs); no auth on pipeline/result endpoints | Security |
| D18 | Conflicting schemas in artifacts | `pipeline_cache.json` vs `pipeline_output.json` (different top-level shapes) | Consumer confusion; stale output file |
| D19 | No test coverage | glob `**/test_*.py`, `**/*_test.py`: no files | Regressions undetectable |

## 8.4 Low Debt

| # | Debt | Evidence | Why it matters |
|---|---|---|---|
| D20 | Empty scaffolding | 11 empty directories, 6 zero-byte files | Misrepresents progress; confuses structure |
| D21 | Empty i18n | `i18n/en.json`, `i18n/th.json` (0 bytes) | Localization absent; ad-hoc script in `manager.html` |
| D22 | Orphaned candidate generator | `ai_engine/generator/candidate_generator.py`; grep shows no callers | Dead code carrying stale-data reads |
| D23 | No `requirements.txt` / README | none present | Environment non-reproducible |
| D24 | Broken/incomplete version control | `.git/` present but `git` reports `fatal: not a git repository` | No history, no rollback |

## 8.5 Debt Scorecard

| Category | Items | Severity-weighted impact |
|---|---|---|
| Data integrity | D3, D4, D8, D18 | **Critical** — invalidates metrics and predictions |
| AI correctness | D1, D7, D10, D11, D12 | **Critical** — signature features non-functional or wrong |
| Architecture | D5, D6, D16 | **High** — version skew, broken routes, coupling |
| Security | D13, D15, D17 | **High** — credentials, XSS, no auth |
| Maintainability | D9, D14, D19, D20-D24 | **Medium-High** — duplication, zero tests, dead code |

## 8.6 Payoff-Versus-Effort Priority (for remediation planning)

| Priority | Debt items | Rationale |
|---|---|---|
| Do first | D1, D2, D3, D4 | Highest integrity impact, contained scope |
| Do second | D7, D8, D10, D18 | Fixes correctness of the core engine |
| Do third | D5, D6, D9, D14, D16 | Consolidation and architecture |
| Do fourth | D11, D12, D13, D15, D17 | Calibration, attribution, security hardening |
| When convenient | D19-D24 | Tests, docs, cleanup |

**Cross-references:** the full remediation order is laid out in `reports/audit/10-development-roadmap.md`; evidence details in `reports/audit/05-analytics-audit.md` and `reports/audit/06-ai-audit.md`.
