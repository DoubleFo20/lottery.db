# 14 — AI Context

**Status: Draft**

## Purpose

Provides AI assistants with the essential domain and integrity context in one compact place, so every session starts from the same ground truth without re-reading the whole codebase.

## Scope

- Domain model and key data facts.
- Integrity constraints that must never be regressed.
- Does not define operating rules (`AGENTS.md`, `AI_RULES.md`) or navigation (`README.md`).

## Responsibilities

- Keep facts current as the system evolves.
- Stay compact; defer detail to the reference docs.
- Prevent AI work from contradicting established ground truth.

## System in One Line

A Thai-state-lottery analysis and prediction suite that cleans draw history, analyzes patterns, computes probabilities, fuses them into candidates, and presents results in dashboards.

## Canonical Pipeline

```
Historical Database → Cleaning → Analytics → Probability → Prediction → Dashboard
```

Details and per-stage status: `docs/reference/06_AI_PIPELINE.md`.

## Domain Terms

| Term | Meaning |
|---|---|
| Draw / งวด | One lottery drawing event (one 6-digit first-prize result) |
| First prize | The 6-digit winning number; the primary prediction target |
| History | The master dataset of past draws |
| Feature dataset | Engineered per-draw attributes derived from history |
| Candidate | A predicted number produced by the pipeline |
| Actual result | The real winning number for a draw, used for evaluation |

## Key Data Facts

- `database/dataset/lottery_history.csv`: **467 draws**, `2006-12-30` → `2026-07-01`, descending order. Ground truth.
- Feature/temporal datasets (`lottery_features.csv`, `lottery_temporal_features.csv`): **459 rows**, latest `2026-03-01` — **stale by 8 draws**.
- `database/predictions/ensemble_weights.json`: 8 weights, **never consumed** by the predictor (broken self-learning loop).
- `database/predictions/prediction_history.json`: contains a **fabricated actual** (`"123456"` for `2026-04-01`; real prize `292514`).

## Integrity Constraints (never regress)

1. Metrics must derive from real draw results, never fabricated actuals.
2. Adapted weights must actually affect predictions.
3. Transition probabilities must encode `P(next_draw | current_draw)` in chronological order.
4. Feature datasets must match the master history.
5. One canonical prediction-log schema and one canonical API layer.

## References

- `docs/reference/00_PROJECT_OVERVIEW.md` — project overview
- `docs/reference/02_SYSTEM_ARCHITECTURE.md` — architecture
- `docs/reference/04_DATABASE_SCHEMA.md` — data layer
- `docs/reference/06_AI_PIPELINE.md` — pipeline and contracts
- `AI_RULES.md` — rules of engagement
- `AGENTS.md` — operating manual
