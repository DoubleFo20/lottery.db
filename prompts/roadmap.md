# Prompt — Roadmap

**Status: Draft**

## Purpose

Plans phases and priorities, producing updates to the roadmap, new ADRs, and a backlog of specs.

## When to Use

- At the start of each planning cycle.
- After audits, when priorities shift.
- Before starting a new phase of `docs/governance/08_ROADMAP.md`.

## Inputs

- `reports/audit/` — current snapshot findings.
- `docs/governance/10_TECHNICAL_DEBT.md` — debt register.
- `docs/governance/08_ROADMAP.md` — current plan.
- `decisions/` — existing ADRs.

## Outputs

- Updated `docs/governance/08_ROADMAP.md` with phase/item statuses.
- New ADRs in `decisions/` for significant decisions.
- A backlog of spec candidates under `specs/`.

## Guardrails

- Documentation only: no code, no implementation.
- Every priority change must cite evidence from the audit or debt register.
- Preserve the dependency ordering (Phase 0 → 1 → 2 → ...).

## Procedure

1. Read the mandatory context per `AGENTS.md`.
2. Review audit findings and debt register.
3. Propose phase priorities with rationale.
4. Update roadmap statuses and draft new ADRs.
5. Flag spec candidates for `prompts/spec.md`.

## References

- `AGENTS.md` — guardrails
- `docs/governance/08_ROADMAP.md` — the plan to update
- `docs/governance/10_TECHNICAL_DEBT.md` — debt input
- `decisions/0000-architecture-decision-record-template.md` — ADR format
