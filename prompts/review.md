# Prompt — Review

**Status: Draft**

## Purpose

Reviews a diff or pull request against its spec, the coding standards, and the API contract. Read-only.

## When to Use

- Before merging any change.
- After builds or refactors.

## Inputs

- The diff/PR under review.
- The relevant spec: `specs/<area>/<feature>.md`.
- `docs/governance/11_CODING_STANDARDS.md`.
- `docs/reference/05_API_SPECIFICATION.md` (if API affected).

## Outputs

- Review findings: blockers, suggestions, and approvals.
- Verdict against the definition of done in `docs/governance/12_TESTING_STRATEGY.md`.

## Guardrails

- Read-only: never modify the diff or repository.
- Evidence rule: cite `file:line` for every finding.
- Verify tests/verification evidence is present before approving.

## Procedure

1. Read the mandatory context per `AGENTS.md`.
2. Check the diff against the spec scope.
3. Check adherence to coding standards and API contract.
4. Confirm tests and verification are present.
5. Produce a clear verdict.

## References

- `AGENTS.md` — guardrails
- `docs/governance/11_CODING_STANDARDS.md` — standards
- `docs/governance/12_TESTING_STRATEGY.md` — definition of done
- `docs/reference/05_API_SPECIFICATION.md` — API contract
