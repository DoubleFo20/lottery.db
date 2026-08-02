# 02 — System Architecture

**Status: Draft**

## Purpose

Describes the system's architecture: conceptual layers, data flows, folder map, and layer rules. This is the canonical reference for design and refactoring decisions.

## Scope

- Conceptual architecture and layer boundaries.
- Data-flow diagrams, including known broken paths.
- Folder map (current state).
- Layer rules that implementation must respect.

## Responsibilities

- Maintain an accurate picture of how the system is structured today.
- Record layer-boundary rules to prevent regressions.
- Track the target layout for the future `src/` migration (see `decisions/0001-target-source-layout.md`).

## Conceptual Layers

1. **Data layer** — CSV datasets, JSON artifacts, MySQL schema (`database/`).
2. **Scraping / pipeline** — history expansion, scheduled updates (`ai_engine/scrapers/`).
3. **Analytics engines** — statistics, patterns, heatmaps, backtest, XAI (`analytics/`).
4. **Ensemble prediction** — signal fusion and candidate generation (`ensemble_model/`).
5. **Self-learning** — evaluation and weight adaptation (`ai_engine/self_learning*.py`).
6. **Trend reporting** — streak/spike/surge detection (`trend_scanner/`).
7. **API / orchestration** — PHP API invoking Python (`api/`, `backend/`).
8. **Presentation** — static dashboards (`dashboard/`).

## Data Flows

### Canonical pipeline (target)

The system is intended to run as six sequential stages:

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

Each stage maps to existing modules and remediation phases; details are in `docs/reference/06_AI_PIPELINE.md`.

### Self-learning loop (currently broken)
```
scrape → lottery_history.csv
       → feature_engineering → lottery_features.csv
       → temporal_weight_engine → lottery_temporal_features.csv
       → predictor.py (hardcoded WEIGHTS — line 51)
       → prediction_history → prediction_history.json
       → performance_analyzer → accuracy_report.json
       → self_learning → prediction_log.json
       → self_learning_manager → ensemble_weights.json   [written]
       → (predictor) ...                                 [never read — BROKEN]
```
Remediation tracked in `docs/governance/08_ROADMAP.md` Phase 1.

### Prediction pipeline (functional)
```
api/predict.php → run_pipeline.py → predict_pipeline.py
  → probability, pattern, heatmap, monte_carlo, temporal, trend, XAI engines
  → pipeline_cache.json → dashboards
```

## Folder Map (current)

```
ai_engine/      scraping, scheduling, self-learning, candidate generation
analytics/      statistical engines, pipeline, XAI, backtest
ensemble_model/ ensemble predictor
trend_scanner/  trend analysis
api/            PHP API + CLI helpers
backend/        PHP API + config
dashboard/      static HTML/JS dashboards
database/       CSV datasets, JSON artifacts, schema.sql
frontend/       empty scaffolding (not implemented)
reports/        audit snapshot (read-only)
docs/           Project OS documentation (reference + governance)
decisions/      architecture decision records
prompts/        AI workflow playbooks
specs/          feature blueprints (per area)
```

Note: this folder map reflects the current layout. The target layout for code is defined in `decisions/0001-target-source-layout.md`.

## Layer Rules

1. No business logic embedded in HTML dashboards; shared logic lives in scripts.
2. The web layer must not block on synchronous Python process invocation (see `docs/governance/08_ROADMAP.md` Phase 3).
3. A single canonical API layer must be used; duplicate API layers are a defect (see `docs/governance/10_TECHNICAL_DEBT.md` D5).
4. Data access should go through a single abstraction before any new storage work (see `docs/governance/10_TECHNICAL_DEBT.md`).
5. Target layout for code is defined in `decisions/0001-target-source-layout.md`; do not create `src/` until migration begins.

## References

- `docs/reference/06_AI_PIPELINE.md` — pipeline details
- `docs/reference/07_ANALYTICS_ENGINE.md` — engine catalog
- `docs/reference/04_DATABASE_SCHEMA.md` — data layer
- `docs/reference/05_API_SPECIFICATION.md` — API contract
- `docs/governance/08_ROADMAP.md` — remediation phases
- `docs/governance/10_TECHNICAL_DEBT.md` — debt register
- `decisions/0001-target-source-layout.md` — target layout
- `reports/audit/03-architecture-audit.md` — audit snapshot
