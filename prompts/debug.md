# Prompt — Debug

**Status: Draft**

## Purpose

Performs evidence-first root-cause analysis of defects or unexpected behavior.

## When to Use

- Bug reports or failing tests.
- Unexpected data artifacts (e.g., the fabricated actuals defect).
- Behavior differences between environments.

## Inputs

- Description of the observed behavior.
- Relevant logs and data artifacts.
- Affected code areas.

## Outputs

- Root-cause statement with `file:line` evidence.
- Reproduction steps or test demonstrating the cause.
- Recommended fix mapped to a roadmap item or debt ID.

## Guardrails

- Evidence rule: cite `file:line`; state "Not enough evidence" when unverifiable.
- Do not fix in this pass unless asked; diagnose first.
- No guessing about intent.

## Procedure

1. Read the mandatory context per `AGENTS.md`.
2. Reproduce or trace the failure path.
3. Isolate the root cause with evidence.
4. Write a failing test if feasible.
5. Report the cause and recommended remediation.

## References

- `AGENTS.md` — guardrails
- `docs/reference/02_SYSTEM_ARCHITECTURE.md` — data flows
- `docs/governance/08_ROADMAP.md` — where the fix lands
- `docs/governance/10_TECHNICAL_DEBT.md` — debt linkage
