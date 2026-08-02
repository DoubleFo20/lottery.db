# 11 — Coding Standards

**Status: Draft**

## Purpose

Defines coding and contribution conventions for the Lottery project. Enforced by `prompts/build.md`, `prompts/review.md`, and `prompts/test.md`.

## Scope

- Language style (Python, PHP, JavaScript/HTML).
- Repository conventions.
- Commit and pull-request rules.

## Responsibilities

- Provide the single standard for code and contributions.
- Update when the team agrees on a new convention.
- Serve as the acceptance checklist for reviews.

## Python

- Follow PEP 8.
- No comments unless they explain non-obvious decisions; no commented-out code.
- All modules parse cleanly (`python -m py_compile`).
- No ML-library imports unless the module genuinely uses them (see `docs/reference/06_AI_PIPELINE.md`).
- Paths must reference the canonical data access layer; no new hardcoded CSV reads (see `docs/reference/02_SYSTEM_ARCHITECTURE.md`).

## PHP

- Follow PSR-12.
- No `shell_exec` in new code (see `docs/reference/05_API_SPECIFICATION.md`).
- Database credentials only via environment variables; never hardcoded (D13).

## JavaScript / HTML

- Shared logic lives in script files, not inline in HTML.
- Escape all dynamically inserted content before DOM insertion; prefer `textContent` (D15).
- Reference a single canonical API base URL (D5).

## Repository Conventions

- Do not commit secrets, keys, or tokens.
- Do not commit generated artifacts unless required for the app to run.
- One prediction-log schema; do not add new log writers without consolidation (D8, D11).

## Commits

- Small, atomic commits with a single concern.
- Message style: `type(scope): summary` where type is `fix`, `feat`, `refactor`, `test`, `docs`, `chore`.
- Reference the roadmap item or debt ID when relevant (e.g., `fix(ai): load ensemble weights (R4)`).

## Pull Requests

- Must pass verification (lint/compile + relevant tests) per `docs/governance/12_TESTING_STRATEGY.md`.
- Must be reviewed against the relevant spec and standards.
- Must not mix unrelated changes.

## References

- `docs/governance/12_TESTING_STRATEGY.md` — verification requirements
- `docs/reference/05_API_SPECIFICATION.md` — API constraints
- `docs/governance/10_TECHNICAL_DEBT.md` — debt-driven constraints
- `AGENTS.md` — AI guardrails
