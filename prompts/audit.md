# Prompt — Audit

**Status: Draft**

## Purpose

Runs a read-only, evidence-based audit of the repository and produces a snapshot plus updates to the living debt register.

## When to Use

- Periodically, or before major roadmap phases.
- After significant refactors or data changes.
- When the team needs a fresh integrity snapshot.

## Inputs

- `reports/audit/` — previous snapshot
- `docs/governance/10_TECHNICAL_DEBT.md` — existing debt register
- `docs/governance/08_ROADMAP.md` — phase status

## Outputs

- New/updated audit snapshot under `reports/audit/`.
- Proposed updates to `docs/governance/10_TECHNICAL_DEBT.md` and `docs/governance/08_ROADMAP.md`.

## Guardrails

- Read-only: never modify source code, data, or configuration.
- Evidence rule: cite `file:line`; state "Not enough evidence" when unverifiable.
- Never guess or speculate about intent.

## Procedure

1. Read the mandatory context per `AGENTS.md`.
2. Inventory current files and data artifacts.
3. Verify key claims (dataset counts, weight consumption, API paths).
4. Produce findings with evidence.
5. Recommend debt register and roadmap updates.

## References

- `AGENTS.md` — guardrails
- `docs/governance/10_TECHNICAL_DEBT.md` — register to update
- `reports/audit/01-executive-summary.md` — snapshot format reference
