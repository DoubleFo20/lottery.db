# Prompt — Test

**Status: Draft**

## Purpose

Adds test coverage per the testing strategy. Establishes and maintains the test pyramid for the project.

## When to Use

- When a build produces new code.
- When coverage gaps are identified (e.g., D19).
- After refactors, to lock behavior.

## Inputs

- `docs/governance/12_TESTING_STRATEGY.md` — standards.
- Code under test.
- Known data fixtures (small, real datasets).

## Outputs

- Unit/integration/evaluation tests.
- Test fixtures under a `tests/` area.

## Guardrails

- Tests must be deterministic and use real data or small fixtures.
- Evaluation tests must be walk-forward and use real actuals (never fabricated).
- Do not modify production code unless fixing a defect found by the tests.

## Procedure

1. Read the testing strategy.
2. Identify the test layer (unit/integration/evaluation).
3. Write tests with fixtures.
4. Run the suite; ensure green.
5. Report coverage of the touched module.

## References

- `AGENTS.md` — guardrails
- `docs/governance/12_TESTING_STRATEGY.md` — strategy
- `docs/reference/04_DATABASE_SCHEMA.md` — fixtures source
- `docs/governance/11_CODING_STANDARDS.md` — conventions
