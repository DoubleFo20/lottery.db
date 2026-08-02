# 04 — Database Schema

**Status: Draft**

## Purpose

Documents the data layer: MySQL schema, the CSV/JSON dataset artifacts, and the data-staleness contract. This is the reference for any work touching data.

## Scope

- MySQL schema (`database/schema.sql`).
- Dataset artifacts under `database/dataset/`, `database/predictions/`, `database/backtest/`, `database/simulation/`.
- Staleness and integrity expectations.

## Responsibilities

- Keep table and artifact documentation accurate as the schema evolves.
- Document known data-integrity defects and their status.
- Define which artifact is the source of truth for each concern.

## SQLite / SQLAlchemy Layer

The foundation API (Sprint 2.1) introduces a local SQLite database managed via SQLAlchemy 2.x ORM and Alembic migrations.

| Table | Purpose | Model |
|---|---|---|
| `lottery_draws` | Draw results by date (unique `draw_date`) | `app/models/lottery_draw.py` |
| `lottery_number_statistics` | Per-number frequency and hot/cold scores (unique `number`) | `app/models/lottery_number_statistics.py` |
| `prediction_history` | Stored predictions with `predicted_numbers` JSON | `app/models/prediction_history.py` |
| `import_logs` | Import provenance (`rows_imported`, `status`, `error_message`) | `app/models/import_log.py` |

- Repository layer: `app/repositories/` — generic `CRUDBase` plus per-model repositories.
- Migrations: `migrations/` (Alembic); initial migration `ea56edd686c9`.
- Database path: `LOTTERY_DB_PATH` env var (default `database/lottery.sqlite`); `app/database.py` exposes `init()`, `connect()`, `verify()`, `get_db()`.

## MySQL Schema

| Table | Purpose |
|---|---|
| `lottery_results` | Draw results |
| `predictions` | Stored predictions |

Configuration is hardcoded in `backend/config/database.php` (see `docs/governance/10_TECHNICAL_DEBT.md` D13). Note: no module currently reads from MySQL; CSV/JSON files remain the effective source of truth.

## Dataset Artifacts

| Artifact | Content | Status |
|---|---|---|
| `dataset/lottery_history.csv` | Master history: 467 rows, 2006-12-30 → 2026-07-01, descending | Ground truth |
| `dataset/lottery_features.csv` | 459 rows, latest 2026-03-01 | **Stale** (missing 8 draws) |
| `dataset/lottery_temporal_features.csv` | 459 rows, latest 2026-03-01 | **Stale** (missing 8 draws) |
| `predictions/prediction_history.json` / `.csv` | Contains fabricated actual `"123456"` for 2026-04-01 (real: `292514`) | **Defective** |
| `predictions/prediction_log.json` | Second, divergent prediction log | Inconsistent |
| `predictions/ensemble_weights.json` | 8 weights; never consumed by predictor | Broken contract |
| `predictions/pipeline_cache.json` | Pipeline output cache (candidates) | Active |
| `predictions/pipeline_output.json` | Divergent schema from cache | Orphaned |
| `backtest/backtest_report.json` | 359 draws; `accuracy_score: 3766.67` (invalid) | **Defective** |
| `simulation/monte_carlo_results.json` | 100,000 simulations | Active |

## Integrity Contracts

1. Feature datasets must match the master history's row count and latest date.
2. All recorded actual results must match `lottery_history.csv`.
3. `ensemble_weights.json` must be consumed by the predictor (currently not).
4. One canonical prediction-log schema must exist.

Remediation is tracked in `docs/governance/08_ROADMAP.md` Phase 0.

## References

- `database/schema.sql` — schema source
- `app/models/` — SQLAlchemy ORM models (SQLite layer)
- `app/repositories/` — CRUD/repository layer
- `migrations/` — Alembic migrations (SQLite layer)
- `docs/reference/05_API_SPECIFICATION.md` — data exposed via API
- `docs/reference/06_AI_PIPELINE.md` — weight/signal contracts that read these artifacts
- `docs/reference/07_ANALYTICS_ENGINE.md` — engines that produce/consume these artifacts
- `docs/governance/08_ROADMAP.md` — Phase 0 data integrity
- `reports/audit/02-project-inventory.md` — audit snapshot
