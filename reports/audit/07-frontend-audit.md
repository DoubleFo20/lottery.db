# 7. Frontend Audit

**Document type:** Audit report (documentation only)
**Project:** Lottery analysis suite
**Root:** `D:\xampp\htdocs\Lottery`

Scope: the static HTML/JS dashboards (`dashboard/`), the empty modern frontend (`frontend/`), and localization (`i18n/`).

---

## 7.1 Inventory (verified)

| File | Size (bytes) | Role |
|---|---|---|
| `dashboard/app.js` | 7,451 | Dashboard application logic |
| `dashboard/manager.html` | 35,642 | Manager dashboard |
| `dashboard/performance.html` | 19,904 | Performance dashboard |
| `dashboard/strategy.html` | 37,306 | Strategy dashboard |
| `dashboard/charts/` | — | **Empty** |
| `dashboard/components/` | — | **Empty** |
| `frontend/src/` | — | **Empty** (no modern framework code) |
| `frontend/public/` | — | **Empty** |
| `i18n/en.json` | 0 | **Empty** |
| `i18n/th.json` | 0 | **Empty** |

## 7.2 Data Sources Referenced by Dashboards (verified via fetches)

| Dashboard | Data source(s) |
|---|---|
| `manager.html` | `../backend/api/predict.php` (line 493), pipeline cache, etc. |
| `performance.html` | `../analytics/performance.json` (does **not** exist — falls back to root `performance.json`), `prediction_history.json`, `pipeline_output.json` |
| `strategy.html` | `../api/predict.php`, `../analytics/performance.json` (does not exist), `../database/predictions/pipeline_cache.json`, `run_pipeline`, `fetch_result` |
| `app.js` | `/Lottery/api/predict.php` (line 1) |

**Key inconsistency:** three different API paths are used across the four dashboard files (`/Lottery/api/predict.php`, `../backend/api/predict.php`, `../api/predict.php`). Updating one layer while another stays stale will yield version skew.

## 7.3 Schema Mismatch Between Frontend and Data (evidence)

- `app.js:149` assumes an XAI payload shape of `pos.reasons.slice(0, 2)` where each reason is a **string**.
- The actual `database/predictions/pipeline_cache.json` shape is `explanation.positions[].reasons.{th, en}` (objects with two localized strings).
- Result: the dashboard's reason-rendering logic does not match the data it consumes, producing broken/empty explanation display.

## 7.4 Security Findings (evidence)

| Finding | Evidence | Severity |
|---|---|---|
| Reflected XSS via unescaped `innerHTML` of API-sourced candidate numbers | `app.js:71-83`, `manager.html:592-600` | Medium (API content is internal, but no escaping) |
| Mixed trusted/derived content rendered into DOM | candidate numbers, explanations, heat values injected via template literals | Medium |

## 7.5 Frontend Structure & Maintainability

1. Dashboard logic is duplicated between `app.js` and inline scripts embedded in each HTML file; `manager.html` also embeds a TH/EN localization replacement script rather than using `i18n/`.
2. The intended component architecture is absent: `dashboard/components/` and `dashboard/charts/` are empty, and there is no bundler, module system, or build step.
3. `frontend/` (a separate modern frontend) is entirely unimplemented (empty `src/` and `public/`).

## 7.6 Localization

- `i18n/en.json` and `i18n/th.json` are zero-byte placeholders.
- Actual localization is ad-hoc string replacement embedded in `manager.html`.
- No language-selection or persistence mechanism found.

## 7.7 Frontend Assessment Scores

| Category | Score | Rationale |
|---|---|---|
| Functional coverage | **5 / 10** | KPI, candidates, trends, weights, streaks renderable; but broken XAI rendering and nonexistent metrics endpoint |
| Consistency | **3 / 10** | Three API base paths; two performance.json candidates |
| Security | **5 / 10** | No escaping on dynamic content |
| Modularity | **3 / 10** | Logic duplicated across HTML files; empty components dirs |
| Modern frontend | **0 / 10** | `frontend/` is empty |

## 7.8 Risks

| Risk | Level |
|---|---|
| Version skew from multiple API paths | High |
| XAI schema mismatch → broken explanations | High |
| Unescaped DOM insertion | Medium |
| Nonexistent `analytics/performance.json` → silent fallback to possibly wrong file | Medium |
| No tests, no build step, no lint | High (maintainability) |

## 7.9 Recommendations (documentation only)

1. Consolidate all dashboard fetch calls to a single API base URL (and single endpoint for performance metrics).
2. Align frontend rendering to the actual cache schema (`reasons.{th,en}`) or add a schema-versioned API contract.
3. Escape all dynamically inserted values before `innerHTML`; prefer `textContent`.
4. Move shared logic into `app.js` (or `components/`) and remove duplicated inline scripts.
5. Implement `i18n/` properly or remove the empty files.
6. Either implement or remove the empty `frontend/` scaffolding.

**Cross-references:** `reports/audit/03-architecture-audit.md` §3.3, `reports/audit/09-gap-analysis.md`, `reports/audit/10-development-roadmap.md`.
