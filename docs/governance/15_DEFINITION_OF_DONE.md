# 15 — Definition of Done

**Status: Draft**

## Purpose

Defines a single, unambiguous "done" for every change so completion is verifiable rather than subjective.

## Scope

Applies to all changes: code, documentation, data, and process artifacts. Used by operators and AI assistants alike.

## Responsibilities

- Provide the acceptance checklist for any merge.
- Enforce the project rules (`docs/governance/17_PROJECT_RULES.md`) and AI rules (`AI_RULES.md`).
- Link each criterion to the governing document.

## Definition of Done Checklist

A change is **done** only when all of the following hold:

| # | Criterion | Rule / Reference |
|---|---|---|
| 1 | References an approved spec or roadmap item | `AI_RULES.md` Rule 3; `specs/` |
| 2 | Does not invent features | `AI_RULES.md` Rule 1 |
| 3 | Does not modify architecture without approval | `AI_RULES.md` Rule 2; `decisions/` |
| 4 | Tests exist and pass | `AI_RULES.md` Rule 4; `docs/governance/12_TESTING_STRATEGY.md` |
| 5 | Documentation updated (status + references) | `AI_RULES.md` Rule 5; `AGENTS.md` doc hygiene |
| 6 | Backward compatible or has an approved migration path | `AI_RULES.md` Rule 6; `docs/reference/05_API_SPECIFICATION.md` |
| 7 | All reported metrics derive from real actuals | `AI_RULES.md` Rule 7; `docs/reference/04_DATABASE_SCHEMA.md` |
| 8 | Standards followed and evidence cited | `docs/governance/11_CODING_STANDARDS.md` |
| 9 | Uncertainties were asked, not guessed | `AI_RULES.md` Rule 8 |
| 10 | Human sign-off recorded | `AGENTS.md` guardrail 4 |

## Usage

- `prompts/review.md` checks the checklist before approving a diff.
- `prompts/build.md` uses it as the exit criterion.
- Operators use it as the merge gate.

## References

- `AI_RULES.md` — rules operationalized here
- `docs/governance/17_PROJECT_RULES.md` — project process rules
- `docs/governance/11_CODING_STANDARDS.md` — conventions
- `docs/governance/12_TESTING_STRATEGY.md` — verification standards
- `prompts/review.md` — review workflow
