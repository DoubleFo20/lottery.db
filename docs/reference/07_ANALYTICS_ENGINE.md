# 07 — Analytics Engine

**Status: Draft**

## Purpose

Catalogs the analytics engines: purpose, inputs, outputs, and current health. Prevents duplicate implementations and guides reuse.

## Scope

- All modules in `analytics/`.
- Ensemble and trend modules that feed analytics.
- Known defects per module.

## Responsibilities

- Maintain an accurate catalog as engines change.
- Record health and integrity status per module.
- Flag overlaps that should be consolidated.

## Engine Catalog

| Module | File | Purpose | Health |
|---|---|---|---|
| Probability engine | `analytics/probability_engine.py` | Digit/pair/triple frequencies, lift, z-scores | Sound |
| Advanced probability | `analytics/probability_advanced.py` | Supplementary statistics | Sound |
| Pattern engine | `analytics/pattern_engine.py` | Pattern analysis | Sound (not wired into pipeline) |
| Heatmap engine | `analytics/heatmap_engine.py` | Heatmap analysis | Sound |
| Monte Carlo engine | `analytics/monte_carlo_engine.py` | Simulation | Sound |
| Feature engineering | `analytics/feature_engineering.py` | Builds `lottery_features.csv` | Writes stale data (Phase 0) |
| Temporal weight engine | `analytics/temporal_weight_engine.py` | Builds temporal features | Writes stale data (Phase 0) |
| Result fetcher | `analytics/result_fetcher.py` | Fetches draw results | Fragmented verification |
| Performance analyzer | `analytics/performance_analyzer.py` | Builds accuracy metrics | Derives from defective data |
| Explainable AI | `analytics/explainable_ai.py` | Per-position explanations | Recomputes factors |
| Backtest engine | `analytics/backtest_engine.py` | Model evaluation | **Defective** (random + broken formula) |
| Prediction pipeline | `analytics/predict_pipeline.py` | Pipeline orchestrator | Pattern step non-functional |
| Prediction history | `analytics/prediction_history.py` | Logs predictions/actuals | Stores fabricated actuals |
| Strategy optimizer | `analytics/strategy_optimizer.py` | Strategy optimization | Limited integration |

## Overlaps to Consolidate

- Probability signals are re-implemented in the predictor, XAI, and advanced probability modules.
- Scraper/parser logic is duplicated in three files (see `docs/governance/10_TECHNICAL_DEBT.md` D9).

## References

- `docs/reference/06_AI_PIPELINE.md` — how engines feed the pipeline
- `docs/reference/04_DATABASE_SCHEMA.md` — data artifacts produced/consumed
- `docs/governance/08_ROADMAP.md` — remediation phases
- `docs/governance/10_TECHNICAL_DEBT.md` — engine-related debt (e.g., D9, D10)
- `docs/governance/12_TESTING_STRATEGY.md` — engine test coverage
- `reports/audit/05-analytics-audit.md` — audit snapshot
