# Specs — Index & Lifecycle

**Status: Draft**

## Purpose

Defines how feature blueprints in `specs/` are created, approved, implemented, and archived.

## Scope

- Spec areas: `analytics/`, `prediction/`, `backend/`, `frontend/`, `database/`.
- Lifecycle and status fields.
- Relationship to prompts and roadmap.

## Responsibilities

- Maintain the spec template and area conventions.
- Track each spec's lifecycle status.
- Ensure specs are the sole input for `prompts/build.md`.

## Spec Lifecycle

```
idea → spec.md → Draft → approved → build.md → Implemented → Superseded/Archived
```

## Status Fields

| Status | Meaning |
|---|---|
| Draft | Being written; not approved |
| Approved | Ready for implementation |
| Implemented | Code delivered and verified |
| Superseded | Replaced by another spec |

## Required Spec Sections (per `_TEMPLATE.md`)

- Purpose
- Scope
- Inputs / Outputs
- Acceptance Criteria
- Status
- References

## Area Conventions

| Area | Typical content |
|---|---|
| `analytics/` | New engines, evaluation, backtest changes |
| `prediction/` | Pipeline, ensemble, self-learning, trend signals |
| `backend/` | API, config, database access changes |
| `frontend/` | Dashboard and UI changes |
| `database/` | Schema, datasets, migrations |

## References

- `specs/_TEMPLATE.md` — spec structure
- `prompts/spec.md` — spec-writing workflow
- `prompts/build.md` — implementation workflow
- `docs/governance/08_ROADMAP.md` — roadmap linkage
