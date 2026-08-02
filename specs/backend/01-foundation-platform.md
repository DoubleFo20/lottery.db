# Spec — Foundation Platform (Sprint 1)

Status: Approved

## Purpose

Establishes a runnable project foundation: a React/Vite/TypeScript/TailwindCSS frontend, a Python FastAPI backend, SQLite storage, a health-check API, and the full developer-experience toolchain. This is the build contract for Sprint 1 and the only scope implemented.

## Scope

### In scope

- Frontend: React + Vite + TypeScript + TailwindCSS, located in `frontend/`.
- Backend: Python + FastAPI + virtual environment, located in `backend/` (new `app/`, `tests/` subdirs; frozen PHP in `backend/api/` and `backend/config/` is untouched).
- Database: SQLite, file created at runtime under `database/` (`database/lottery.sqlite`).
- API: `GET /health` returning `{"status": "ok"}`.
- Frontend display: "Backend Connected" when `/health` is reachable.
- Developer experience: ESLint, Prettier (frontend); Ruff, Black, Pytest (backend); npm scripts.

### Out of scope (explicitly prohibited by Sprint 1)

- No AI implementation, prediction engine, analytics, trend scanner, ensemble model, or dashboard widgets.
- No modifications to the frozen PHP API layer, frozen docs, or frozen architecture (Project OS v1.0).
- No creation of `src/` (deferred to migration per `decisions/0001-target-source-layout.md`).
- No unfinished placeholders; everything must compile and run.

## Inputs

- `docs/reference/02_SYSTEM_ARCHITECTURE.md`, `docs/reference/05_API_SPECIFICATION.md`, `docs/reference/14_AI_CONTEXT.md` — frozen context
- `docs/governance/11_CODING_STANDARDS.md`, `12_TESTING_STRATEGY.md`, `15_DEFINITION_OF_DONE.md` — standards
- `AI_RULES.md`, `AGENTS.md` — rules of engagement
- `decisions/0001-target-source-layout.md` — target layout (deferred)
- Existing `frontend/` scaffolding (empty `src/`, `public/`, `package-lock.json` named `frontend`)

## Outputs

- `frontend/` — Vite + React + TS + Tailwind app with ESLint/Prettier/npm scripts and a "Backend Connected" status view.
- `backend/` — FastAPI app (`app/`), pytest suite (`tests/`), virtual environment (`.venv/`), Ruff/Black config, pinned requirements.
- `database/lottery.sqlite` — SQLite database created at backend startup.

## Acceptance Criteria

1. `GET /health` returns HTTP 200 with body `{"status": "ok"}`.
2. Frontend displays "Backend Connected" when the backend is reachable.
3. Backend verification passes: `ruff`, `black --check`, and `pytest`.
4. Frontend verification passes: `tsc -b` (via `npm run build`), `eslint`, and `prettier --check`.
5. Backend and frontend both compile and run locally.
6. No frozen files modified; no AI/prediction/analytics/trend/ensemble/dashboard code added.

## Dependencies

- Runtime: Python 3.12, Node 24, npm 11.
- Backend packages: FastAPI, Uvicorn; dev: Pytest, Httpx (TestClient), Ruff, Black.
- Frontend packages: React, React DOM; dev: Vite, TypeScript, TailwindCSS, ESLint, Prettier.

## References

- `specs/_TEMPLATE.md` — spec structure
- `docs/governance/15_DEFINITION_OF_DONE.md` — acceptance checklist
- `docs/reference/05_API_SPECIFICATION.md` — API constraints (CORS allow-list, no open `*`)
- `docs/governance/11_CODING_STANDARDS.md` — conventions
- `prompts/build.md` — build workflow
