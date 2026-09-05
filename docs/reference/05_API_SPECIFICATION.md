# 05 — API Specification

**Status: Draft — updated 2026-08-07**

## Purpose

Defines the canonical API contract for the Lottery system. Resolves the current three divergent API paths into one authoritative specification.

## Scope

- Endpoints, methods, parameters, and payloads.
- Authentication and security requirements.
- Execution model (how Python is invoked).
- Does not implement the API; it specifies it.

## Responsibilities

- Act as the single source of truth for API behavior.
- Record known divergence and its remediation status.
- Constrain implementation work (`prompts/build.md`) and review (`prompts/review.md`).

## Current State

The foundation FastAPI currently exposes these read-only endpoints:

| Method | Path | Response |
|---|---|---|
| GET | `/health` | `{"status": "ok"}` |
| GET | `/history?offset=0&limit=20` | `ApiResponse` containing newest-first core draw records and pagination metadata; `limit` is constrained to 1–100 |

The history endpoint is implemented by `backend/app/main.py` and reads the seeded SQLite `lottery_draws` table. It does not replace the legacy PHP prediction API described below.

Two near-duplicate PHP API layers exist and are referenced inconsistently:

| Path | Used by | Status |
|---|---|---|
| `backend/api/predict.php` | `dashboard/manager.html:493` | Candidate canonical layer |
| `api/predict.php` | `dashboard/app.js:1`, `dashboard/strategy.html` | Duplicate |
| `database/api/predict.php` | none | **Broken** (missing include) |

Consolidation is tracked as `docs/governance/10_TECHNICAL_DEBT.md` D5/D6 and `docs/governance/08_ROADMAP.md` Phase 2.

## Canonical Endpoints (target)

| Method | Path | Action | Notes |
|---|---|---|---|
| GET | `/predict.php?action=predict` | Return cached predictions | Reads `pipeline_cache.json` |
| GET | `/predict.php?action=history` | Return prediction history | Single log schema |
| GET | `/predict.php?action=analytics` | Return analytics payload | |
| POST | `/predict.php?action=run_pipeline` | Run pipeline | Should move to worker (Phase 3) |
| POST | `/predict.php?action=fetch_result` | Fetch latest draw result | Should move to worker (Phase 3) |

## Payload Conventions

- Predictions: `candidates` with `number`, `score`, `digits`, `confidence`.
- Explanations: `explanation.positions[].reasons.{th,en}` (localized objects).
- One prediction-log schema across all writers (see `docs/reference/04_DATABASE_SCHEMA.md`).

## Security Requirements (target)

1. Authentication on all write-triggering actions.
2. CORS restricted to an allow-list of origins.
3. No synchronous `shell_exec` from the web layer (see `docs/governance/08_ROADMAP.md` Phase 3).
4. All dynamic values escaped at render time (frontend).

## References

- `specs/backend/02-lottery-history.md` — FastAPI history contract

- `backend/api/predict.php` — reference implementation
- `docs/reference/02_SYSTEM_ARCHITECTURE.md` — layer rules
- `docs/reference/04_DATABASE_SCHEMA.md` — data served by the API
- `docs/governance/10_TECHNICAL_DEBT.md` — D5, D6, D16, D17
- `docs/governance/11_CODING_STANDARDS.md` — PHP conventions
- `docs/governance/12_TESTING_STRATEGY.md` — contract tests
- `reports/audit/04-backend-audit.md` — audit snapshot
