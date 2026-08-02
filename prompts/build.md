# Prompt — Build

**Status: Draft**

## Purpose

Implements an approved spec. Writes code strictly within the spec's scope, following the coding standards.

## When to Use

- When a spec under `specs/` is approved.
- When a roadmap item maps to an approved spec.

## Inputs

- The approved spec: `specs/<area>/<feature>.md`.
- `docs/governance/11_CODING_STANDARDS.md` — conventions.
- Relevant reference docs (architecture, API, AI pipeline).

## Outputs

- Implementation code within the spec's scope.
- Tests per `docs/governance/12_TESTING_STRATEGY.md`.
- Updated doc statuses where relevant.

## Guardrails

- Write only within the approved spec's scope; never touch unrelated files.
- Follow `docs/governance/11_CODING_STANDARDS.md`.
- No secrets; no hardcoded credentials.
- Verify: compile/lint and run relevant tests before finishing.
- Document any deviation from the spec for human review.

## Procedure

1. Read the approved spec and mandatory context per `AGENTS.md`.
2. Implement within scope.
3. Add tests per the testing strategy.
4. Run verification (lint, compile, tests).
5. Report what was done and any deviations.

## References

- `AGENTS.md` — guardrails
- `docs/governance/11_CODING_STANDARDS.md` — standards
- `docs/governance/12_TESTING_STRATEGY.md` — verification
- `specs/_TEMPLATE.md` — spec format
