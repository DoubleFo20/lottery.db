# 08 — Roadmap

**Status: Draft**

## Purpose

Tracks the living development plan: phases, per-item status, and dependencies. Seeded from `reports/audit/10-development-roadmap.md`; this is the operational version that updates as work progresses.

## Scope

- Remediation and feature phases.
- Per-item status and dependencies.
- Cross-links to debt register and ADRs.

## Responsibilities

- Keep each item's status current (Not started / In progress / Done / Blocked).
- Enforce phase ordering and dependencies.
- Provide the planning input for `prompts/roadmap.md`.

## Phase Overview

| Phase | Focus | Status |
|---|---|---|
| 0 | Data integrity (correct actuals, refresh feature datasets) | Not started |
| 1 | Core correctness (self-learning wiring, transition matrix, backtest, pattern step) | Not started |
| 2 | Consolidation & architecture (single API, single log, delete dead code) | Not started |
| 3 | Quality, calibration & security | Not started |
| 4 | Testing, integration & ML | Not started |
| 5 | Process & governance (git re-init, CI gates) | Not started |

## Phase 0 — Data Integrity

- R1. Replace fabricated actuals with real draw results.
- R2. Regenerate feature/temporal datasets to match history (467 rows).
- R3. Re-derive performance metrics from corrected actuals.

## Phase 1 — Core Correctness

- R4. Predictor loads `ensemble_weights.json`.
- R5. Reverse the transition matrix to chronological order.
- R6. Fix the backtest (real predictor, walk-forward, correct formula).
- R7. Fix or remove the pipeline pattern step.
- R8. Add a measured random baseline.

## Phase 2 — Consolidation & Architecture

- R9. Single canonical API layer.
- R10. Delete zero-byte and broken API files.
- R11. Merge the two prediction logs.
- R12. Consolidate scraper parsers.
- R13. Align pipeline cache schemas.
- R14. Resolve empty scaffolding (`frontend/`, dashboard components).
- R15. Add `requirements.txt` and README quickstart.

## Phase 3 — Quality, Calibration & Security

- R16. Calibrate confidence.
- R17. XAI reads model attribution.
- R18. Escape dashboard output; fix XAI schema mismatch.
- R19. Authentication and CORS allow-list.
- R20. Replace synchronous `shell_exec` with a worker.

## Phase 4 — Testing, Integration & ML

- R21. Add test coverage per `docs/governance/12_TESTING_STRATEGY.md`.
- R22. Integrate or remove trend-scanner signals.
- R23. Integrate or remove `candidate_generator.py`.
- R24. Walk-forward evaluation as a permanent gate.
- R25. Optional: real ML on engineered features.

## Phase 5 — Process & Governance

- R26. Re-initialize Git (repo metadata is unusable).
- R27. Add CI gates.
- R28. Publish corrected summary report.

## Dependencies

```
Phase 0 → Phase 1 → Phase 2 → Phase 4
                  ↘ Phase 3 (can overlap Phase 2)
Phase 5: continuous
```

## References

- `reports/audit/10-development-roadmap.md` — audit snapshot
- `docs/governance/10_TECHNICAL_DEBT.md` — debt items referenced by phases
- `docs/reference/05_API_SPECIFICATION.md` — API consolidation (Phase 2, R9)
- `docs/reference/06_AI_PIPELINE.md` — AI correctness (Phase 1, R4–R8)
- `docs/reference/07_ANALYTICS_ENGINE.md` — engine remediation (Phase 1, R6–R7)
- `docs/governance/12_TESTING_STRATEGY.md` — Phase 4 testing work
- `decisions/0001-target-source-layout.md` — target layout ADR
- `docs/reference/00_PROJECT_OVERVIEW.md` — goals
