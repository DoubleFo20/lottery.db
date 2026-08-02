# 06 — AI Pipeline

**Status: Draft**

## Purpose

Documents the AI/prediction pipeline: stages, signal contracts, the ensemble, and the self-learning loop. This is the canonical reference for all AI-related work.

## Scope

- Pipeline stages from history to candidates.
- Signal definitions and the weight contract.
- Self-learning loop and its current broken link.
- Confidence, calibration, and explainability contracts.

## Responsibilities

- Keep the pipeline contract accurate as the AI evolves.
- Record known AI defects and link to remediation.
- Define what "correct" means for each signal.

## Pipeline Stages

The canonical pipeline is a sequence of six stages, each with a clear boundary:

```
Historical Database
        ↓
     Cleaning
        ↓
    Analytics
        ↓
   Probability
        ↓
    Prediction
        ↓
     Dashboard
```

| Stage | Purpose | Current implementation | Status |
|---|---|---|---|
| Historical Database | Ground-truth draw history | `database/dataset/lottery_history.csv` (467 draws) | Working |
| Cleaning | Parse, validate, dedupe, and normalize draw results | Parsers duplicated across scrapers; no validation layer | Weak (see `docs/governance/10_TECHNICAL_DEBT.md` D9) |
| Analytics | Engineered features and statistical analysis (patterns, heatmaps) | `analytics/feature_engineering.py`, `pattern_engine.py`, `heatmap_engine.py` | Partly stale (Phase 0) |
| Probability | Base probability distributions (digit/pair/triple, conditional, transition) | `analytics/probability_engine.py`, `probability_advanced.py` | Working |
| Prediction | Ensemble signal fusion → candidates + confidence | `ensemble_model/predictor.py`, `analytics/predict_pipeline.py` | Defective (see Known Defects) |
| Dashboard | Present candidates, explanations, and trends | `dashboard/`, `pipeline_cache.json` | Working (XAI mismatch) |

### Artifact flow within the pipeline

```
history (lottery_history.csv)
  → feature_engineering      → lottery_features.csv
  → temporal_weight_engine   → lottery_temporal_features.csv
  → ensemble predictor       → candidates (number, score, digits, confidence)
  → explainable_ai           → localized per-position explanations
  → pipeline_cache.json      → dashboards
```

## Signal Contract

The ensemble predictor fuses the following signals with weights (contract in `database/predictions/ensemble_weights.json`):

| Signal | Current weight |
|---|---|
| positional_freq | 0.20 |
| rolling_heat | 0.20 |
| conditional | 0.15 |
| transition | 0.10 |
| pair_lift | 0.10 |
| pattern_hot | 0.10 |
| gap_overdue | 0.08 |
| temporal_trend | 0.07 |

## Known Defects (evidence in `reports/audit/`)

1. **Weights never consumed.** `ensemble_model/predictor.py:51` uses a hardcoded `WEIGHTS` constant; `ensemble_weights.json` is written by self-learning but never loaded by the predictor. This breaks the self-learning loop end-to-end.
2. **Reversed transition matrix.** `predictor.py:123-138` builds `rows[idx] → rows[idx+1]` on a descending-ordered dataset, encoding `P(previous|current)` instead of `P(next|current)`.
3. **Uncalibrated confidence.** Top candidate is always ~100% because confidence is normalized relative to the best candidate, not calibrated against observed outcomes.
4. **Pattern step non-functional.** `analytics/predict_pipeline.py:62` returns the last 5 draws instead of using `pattern_engine.py`.
5. **XAI recomputes factors.** `analytics/explainable_ai.py:44-49` applies its own factor weights instead of reading the model's contributions.
6. **Trend scanner not integrated.** `trend_scanner/` outputs are not consumed as weighted ensemble signals.
7. **Orphaned generator.** `ai_engine/generator/candidate_generator.py` is never invoked by any pipeline.

## Contracts

- **Self-learning:** adapted weights must affect predictions; otherwise the feature is non-functional.
- **Transition:** matrix must encode `P(next_draw | current_draw)` using chronologically ascending rows.
- **Confidence:** must be calibrated or explicitly labeled as relative rank.
- **Explainability:** explanations must reflect the model's actual per-signal contributions.

## References

- `docs/reference/02_SYSTEM_ARCHITECTURE.md` — data flows
- `docs/reference/04_DATABASE_SCHEMA.md` — artifacts the pipeline reads/writes
- `docs/reference/07_ANALYTICS_ENGINE.md` — engine catalog
- `docs/governance/08_ROADMAP.md` — Phase 1 remediation
- `docs/governance/12_TESTING_STRATEGY.md` — evaluation methodology
- `reports/audit/06-ai-audit.md` — audit snapshot
