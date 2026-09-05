# Lottery History Data Flow

Status: Implemented

## Purpose

Make the canonical lottery history visible in the foundation application instead of leaving the SQLite database and Lottery History page empty.

## Scope

- In scope: idempotently seed SQLite from `database/dataset/lottery_history.csv`; expose a paginated read-only FastAPI history endpoint; render the results in the existing Lottery History page.
- Out of scope: database migrations, prediction/analytics behavior, editing draw results, and representing the second front-three/back-three prize that the current SQLite model cannot store.
- Areas affected: backend / frontend / database / documentation.

## Inputs

- `database/dataset/lottery_history.csv` as the canonical history source.
- Existing `LotteryDraw` SQLAlchemy model and repository.
- Existing FastAPI, Axios, TanStack Query, and shared frontend UI components.

## Outputs

- SQLite contains one `lottery_draws` row per canonical draw date, without duplicates across restarts.
- `GET /history?offset=<n>&limit=<n>` returns newest-first draw records and pagination metadata.
- Lottery History renders draw date, first prize, and last-two result with loading, error, empty, and paging states.

## Acceptance Criteria

1. Starting the backend with an empty SQLite database imports all 467 canonical draw rows.
2. Starting the backend again imports zero duplicates.
3. `GET /history` returns HTTP 200, total `467`, and the newest draw first (`2026-07-01`, `751495`, `62`).
4. Invalid pagination values are rejected by FastAPI validation.
5. The Lottery History page displays API-backed rows and paging controls.
6. Relevant backend tests, frontend build, and frontend lint pass.

## Dependencies

- Owner approval recorded in the 2026-08-07 Codex thread.
- Roadmap R14: resolve empty frontend scaffolding.
- `specs/backend/01-foundation-platform.md`.

## References

- `AI_RULES.md`
- `docs/reference/04_DATABASE_SCHEMA.md`
- `docs/reference/05_API_SPECIFICATION.md`
- `docs/governance/11_CODING_STANDARDS.md`
- `docs/governance/12_TESTING_STRATEGY.md`
- `prompts/spec.md`
- `prompts/build.md`
