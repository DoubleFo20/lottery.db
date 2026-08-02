# 16 — Changelog

**Status: Draft**

## Purpose

Records notable changes to the repository in chronological order, giving contributors and AI assistants a reliable history while git metadata is unusable (see `docs/governance/10_TECHNICAL_DEBT.md` D24).

## Scope

- Significant changes to code, data, documentation, and process.
- Does not record every commit; captures milestones and behavior-affecting changes.

## Responsibilities

- Append an entry for each notable change, newest first.
- Reference the relevant roadmap item, debt ID, or ADR where applicable.
- Reconcile with git history once the repository is re-initialized (Phase 5, R26).

## Format

```
## YYYY-MM-DD — Short title

- Change summary with reference (file, roadmap item R#, or debt ID).
- Impact and verification performed.
```

## Entries

### 2026-08-02 — Sprint 2.1: Lottery database foundation

- Added SQLAlchemy 2.x ORM models (`app/models/`): `LotteryDraw`, `LotteryNumberStatistics`, `PredictionHistory`, `ImportLog`, with shared `Base`/`TimestampMixin` (`app/models/base.py`).
- Added Pydantic schemas (`app/schemas/`): create/read variants per model.
- Added repository layer (`app/repositories/`): generic `CRUDBase` (create/get/get_multi/count/remove) plus per-model repositories.
- Refactored `app/database.py` to SQLAlchemy engine/session while preserving `init()`, `connect()`, `verify()` and the `LOTTERY_DB_PATH` env-var contract; `/health` still returns `{"status": "ok"}`.
- Added Alembic (`alembic.ini`, `migrations/`); initial migration `ea56edd686c9` creates all four tables.
- Added CRUD pytest coverage (23 tests passing); ruff and black clean. `requirements.txt` now pins `sqlalchemy==2.0.51`, `alembic==1.18.5`.
- Updated `docs/reference/04_DATABASE_SCHEMA.md` with the SQLite/SQLAlchemy layer.

## References

### 2026-08-02 — Project OS established

- Created the Project Operating System: `README.md`, `AGENTS.md`, `AI_RULES.md`, `docs/` (reference + governance), `decisions/` (ADR-0000, ADR-0001), `prompts/` (8 playbooks), and `specs/` (template + areas: analytics, prediction, backend, frontend, database).
- Added `docs/reference/14_AI_CONTEXT.md`, `docs/governance/15_DEFINITION_OF_DONE.md`, `docs/governance/16_CHANGELOG.md`, and `docs/governance/17_PROJECT_RULES.md` (this file) to complete the minimum viable documentation set.
- Documented the canonical six-stage pipeline (Historical Database → Cleaning → Analytics → Probability → Prediction → Dashboard).
- Seeded documentation from `reports/audit/` (10-document immutable audit snapshot). No application source code was modified.

## References

- `README.md` — project entry point
- `docs/governance/08_ROADMAP.md` — roadmap linkage
- `docs/governance/10_TECHNICAL_DEBT.md` — D24 (git metadata)
- `reports/audit/01-executive-summary.md` — audit snapshot entry
