# ADR-0001 — Target Source Layout

**Status: Draft**

## Context

The audit (`reports/audit/03-architecture-audit.md`) found the codebase split across scattered directories (`ai_engine/`, `analytics/`, `ensemble_model/`, `trend_scanner/`, `backend/`, `api/`, `database/`, `dashboard/`) with 11 empty directories and no data-access abstraction. An empty `src/` at the root would fork the codebase into two realities.

## Decision

Adopt a target source layout for a future migration phase. Do not create `src/` until migration begins (per `docs/governance/08_ROADMAP.md` Phase 2). The target layout groups code by responsibility:

```
src/
├── core/        Python: engines, ensemble, pipeline, self-learning
├── web/         PHP: canonical API layer + config
├── ui/          Dashboard and frontend
├── data/        Schema, migrations, seed fixtures (datasets remain in database/)
└── scripts/     CLI helpers and schedulers
```

## Consequences

- Positive: clear responsibility boundaries; a single importable Python core; one API layer.
- Negative: migration effort; temporary dual-layout period.
- Risks: drift if migration is deferred indefinitely; tests must cover both layouts during transition.

## Alternatives considered

- Create `src/` immediately as empty scaffolding — rejected: forks the codebase.
- Keep current layout permanently — rejected: scattered responsibilities and phantom structure remain.

## References

- `docs/reference/02_SYSTEM_ARCHITECTURE.md` — current architecture
- `docs/governance/08_ROADMAP.md` — Phase 2 (R14)
- `docs/governance/10_TECHNICAL_DEBT.md` — D5, D20
