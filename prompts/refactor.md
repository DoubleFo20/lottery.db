# Prompt — Refactor

**Status: Draft**

## Purpose

Restructures existing code guided by ADRs and the debt register, without changing observable behavior.

## When to Use

- Paying down debt items from `docs/governance/10_TECHNICAL_DEBT.md`.
- Executing consolidation phases of `docs/governance/08_ROADMAP.md`.
- Preparing for the `src/` migration (ADR-0001).

## Inputs

- Debt items to address (`docs/governance/10_TECHNICAL_DEBT.md`).
- `docs/reference/02_SYSTEM_ARCHITECTURE.md` — layer rules.
- Relevant ADRs in `decisions/`.
- Existing tests (or the need to create them first).

## Outputs

- Refactored code preserving behavior.
- Updated tests.
- Updated debt register statuses.

## Guardrails

- Preserve observable behavior; changes must be covered by tests.
- Write only within the refactor's approved scope.
- No new features during refactor.
- Verify with the full relevant test suite.

## Procedure

1. Read the target debt items and architecture rules.
2. Identify behavior-preserving refactor steps.
3. Apply changes in small, verifiable increments.
4. Run tests after each increment.
5. Mark debt items Resolved with references.

## References

- `AGENTS.md` — guardrails
- `docs/governance/10_TECHNICAL_DEBT.md` — debt items
- `decisions/0001-target-source-layout.md` — migration context
- `docs/governance/12_TESTING_STRATEGY.md` — verification
