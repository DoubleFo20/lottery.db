# 4. Backend Audit

**Document type:** Audit report (documentation only)
**Project:** Lottery analysis suite
**Root:** `D:\xampp\htdocs\Lottery`

Scope: PHP API layer, MySQL schema/configuration, and the web↔Python bridge. Analysis of the Python engine code itself is covered in `reports/audit/05-analytics-audit.md` and `reports/audit/06-ai-audit.md`.

---

## 4.1 Inventory (verified)

| File | Size (bytes) | Status |
|---|---|---|
| `backend/config/database.php` | ~200 | Present; hardcoded credentials `localhost / root / "" / lottery_ai` |
| `backend/api/predict.php` | ~4,600 | Full API implementation; uses `shell_exec` (line 66) |
| `backend/api/history.php` | **0** | Empty — declared endpoint does nothing |
| `backend/api/statistics.php` | **0** | Empty — declared endpoint does nothing |
| `api/predict.php` | — | Near-duplicate of `backend/api/predict.php`; CORS `*` (line 7), `shell_exec` (line 28) |
| `api/debug_predict.php` | 1,641 | Debug helper |
| `api/run_pipeline.py` | — | Python CLI pipeline runner (not PHP) |
| `api/performance_api.py` | 42 | Placeholder — effectively no logic |
| `database/api/predict.php` | ~2,700 | **Broken:** includes `../config/database.php`; `database/config/` does not exist |
| `database/api/history.php` | **0** | Empty |
| `database/api/statistics.php` | **0** | Empty |

## 4.2 API Endpoints (as implemented in `backend/api/predict.php`)

| Action | Behavior | Notes |
|---|---|---|
| `predict` | Loads pipeline cache JSON and returns predictions | Reads `database/predictions/pipeline_cache.json` |
| `history` | Returns stored prediction history | Intended data source exists; endpoint also duplicated in empty `history.php` |
| `analytics` | Returns analytics payload | — |
| `run_pipeline` | `shell_exec` invokes Python pipeline | Blocking; spawns process per request |
| `fetch_result` | `shell_exec` invokes result fetch | Returns command output to client (lines 96–104) |

**Note:** The empty `history.php` / `statistics.php` files are unreferenced by the main router, but their very presence alongside a functional router is confusing duplication.

## 4.3 Database Layer

| Aspect | Evidence | Assessment |
|---|---|---|
| Schema | `database/schema.sql` defines `lottery_results` and `predictions` tables | Present |
| Write path | `ai_engine/scrapers/update_scheduler.py:65-70` writes to MySQL with hardcoded credentials | Present |
| Read path | No module found that queries the `predictions` table | **Absent** — CSV JSON files remain the actual source of truth |
| Configuration | `backend/config/database.php` hardcodes `localhost / root / "" / lottery_ai` | Plaintext credentials; duplicated in `update_scheduler.py` |
| `database/api/predict.php` | Includes `../config/database.php` (missing directory `database/config/`) | **Broken include — cannot run** |
| DB runtime state | Table contents not visible from the filesystem | Not enough evidence |

## 4.4 Security Findings (evidence)

| Finding | Evidence | Severity |
|---|---|---|
| Open CORS `Access-Control-Allow-Origin: *` | `api/predict.php:7`, `backend/api/predict.php:27` | Medium |
| No authentication on any endpoint, including `run_pipeline` and `fetch_result` (which trigger Python execution) | action handlers in both PHP APIs | High |
| Server-side command execution `shell_exec('python …')` | `api/predict.php:28`, `backend/api/predict.php:66`; param values are `intval`-clamped (lines 125–127, 140–142) reducing injection risk | Medium (pattern risk remains) |
| Command/script output echoed back to the client | `api/predict.php:96-104`, `backend/api/predict.php` analogous | Medium |
| Plaintext DB credentials in two source files | `backend/config/database.php`, `update_scheduler.py:65-70` | Medium |

## 4.5 Reliability & Concurrency

1. **Blocking `shell_exec`:** each `run_pipeline` / `fetch_result` request spawns a Python process synchronously. Under concurrent dashboard usage this exhausts processes and produces timeouts.
2. **Path coupling:** Python binary path and working directory are assumed; the system is not portable across environments.
3. **No request validation beyond `intval` on `fetch` param:** there is no payload schema validation, rate limiting, or idempotency control.
4. **No error abstraction:** `shell_exec` stderr handling is minimal; failures surface as raw output.

## 4.6 Assessment Summary

| Category | Score | Rationale |
|---|---|---|
| API completeness | **4 / 10** | 3 of 6 PHP files are empty; 1 is broken; 2 are near-duplicates |
| Database usage | **3 / 10** | Schema + write path only; no read consumer; broken include in `database/api/` |
| Security | **3 / 10** | Open CORS, no auth, `shell_exec`, plaintext credentials |
| Reliability | **3 / 10** | Process-per-request, blocking, no caching layer beyond JSON files |

## 4.7 Backend Risks

| Risk | Level |
|---|---|
| Empty endpoints promise features that do not exist | High |
| Broken `database/api/predict.php` include | High |
| Unauthenticated `shell_exec` surface | High |
| Plaintext credentials | Medium |
| No read path to MySQL | Medium |

## 4.8 Recommendations (documentation only)

1. Delete the empty `history.php` / `statistics.php` files and the broken `database/api/` router, or implement them fully.
2. Consolidate to one API layer and standardize the base URL used by dashboards.
3. Replace `shell_exec` with a persistent service/worker that pre-writes JSON caches; dashboards read caches only.
4. Introduce authentication and strict CORS origin allow-listing.
5. Move DB credentials to environment variables; add a read layer over the `predictions` table or remove the MySQL dependency.
6. Add schema validation and rate limiting to API inputs.

**Cross-references:** `reports/audit/03-architecture-audit.md` §3.6, `reports/audit/09-gap-analysis.md` §9.5, `reports/audit/10-development-roadmap.md`.
