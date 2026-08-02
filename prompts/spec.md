# Prompt — Spec

**Status: Draft**

## Purpose

Turns an idea into a feature blueprint under `specs/` that `build.md` can implement and `review.md` can verify.

## When to Use

- Before implementing any new feature or behavior change.
- After planning (`roadmap.md`) identifies a need.

## Inputs

- `docs/reference/` — relevant reference docs (architecture, API, AI pipeline, analytics)
- `docs/governance/08_ROADMAP.md` — phase context
- `docs/governance/10_TECHNICAL_DEBT.md` — debt constraints

## Outputs

- A spec file: `specs/<area>/<feature>.md` following `specs/_TEMPLATE.md`.

## Guardrails

- Documentation only: no code, no schema changes, no implementation.
- Follow the spec template exactly.
- Reference the roadmap items and affected documents.

## Procedure

1. Read the mandatory context per `AGENTS.md`.
2. Identify the area (`analytics`, `prediction`, `backend`, `frontend`, `database`).
3. Write the spec using `specs/_TEMPLATE.md`: goal, scope, inputs/outputs, acceptance criteria, status.
4. Set status `Draft`; obtain approval before `build.md`.

## References

- `specs/_TEMPLATE.md` — spec structure
- `AGENTS.md` — guardrails
- `docs/reference/00_PROJECT_OVERVIEW.md` — domain terms
