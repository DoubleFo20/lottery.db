# 00 — Project Overview

**Status: Draft**

## Purpose

Provides non-technical context for the Lottery project: what it does, why it exists, key domain terms, and current state. Intended as the first document a contributor reads.

## Scope

- Project goals and boundaries.
- Domain terminology used across the codebase and documentation.
- Current status summary (verified by the audit snapshot).
- Does not describe implementation details (see `docs/reference/02_SYSTEM_ARCHITECTURE.md`).

## Responsibilities

- Define the domain vocabulary so all documents and prompts use consistent terms.
- State the project's current integrity status and link to the audit.
- Provide navigation to all other documents.

## Domain Terms

| Term | Meaning |
|---|---|
| Draw / งวด | A single lottery drawing event (one draw = one 6-digit first-prize result) |
| First prize | The 6-digit winning number; the primary prediction target |
| History | The master dataset of past draws |
| Feature dataset | Engineered per-draw attributes derived from history |
| Candidate | A predicted number produced by the pipeline |
| Actual result | The real winning number for a draw, used for evaluation |

## System Pipeline

At a glance, the system is a six-stage pipeline:

```
Historical Database → Cleaning → Analytics → Probability → Prediction → Dashboard
```

Each stage is documented in detail in `docs/reference/06_AI_PIPELINE.md` (stages, contracts, and status) and `docs/reference/02_SYSTEM_ARCHITECTURE.md` (data flows).

## Current Status

- The statistical engines and data collection are functional (see `docs/reference/07_ANALYTICS_ENGINE.md`).
- Four critical integrity defects were identified and are pending remediation:
  1. Self-learning weights are never consumed by the predictor (`docs/reference/06_AI_PIPELINE.md`).
  2. The backtest uses random predictions with an invalid accuracy formula (`docs/governance/08_ROADMAP.md` Phase 1).
  3. Recorded accuracy metrics derive from fabricated actual results (`docs/reference/04_DATABASE_SCHEMA.md`).
  4. Feature datasets are stale by 8 draws (`docs/reference/04_DATABASE_SCHEMA.md`, `docs/governance/08_ROADMAP.md` Phase 0).
- Full evidence is in `reports/audit/`; remediation is tracked in `docs/governance/08_ROADMAP.md`.

## Goals

- Produce transparent, evidence-based predictions with honest confidence.
- Restore and verify the self-learning loop.
- Reach a maintainable, tested, production-ready baseline before adding new features.

## References

- `docs/README.md` — document map and status legend
- `docs/reference/02_SYSTEM_ARCHITECTURE.md` — architecture
- `docs/reference/04_DATABASE_SCHEMA.md` — data layer
- `docs/reference/05_API_SPECIFICATION.md` — API contract
- `docs/reference/06_AI_PIPELINE.md` — AI pipeline
- `docs/reference/07_ANALYTICS_ENGINE.md` — analytics catalog
- `docs/governance/08_ROADMAP.md` — remediation plan
- `docs/governance/10_TECHNICAL_DEBT.md` — debt register
- `reports/audit/01-executive-summary.md` — audit snapshot
- `README.md` — entry point
