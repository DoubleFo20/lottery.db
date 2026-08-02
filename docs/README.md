# Docs — Document Map

**Status: Draft**

## Purpose

Serves as the index and status legend for all living documentation. Ensures every document is discoverable and its lifecycle state is visible.

## Scope

Covers `docs/reference/` and `docs/governance/`. Excludes `decisions/`, `prompts/`, `specs/`, and `reports/audit/`, which have their own indexes.

## Responsibilities

- Maintain the document list and cross-references.
- Define and apply the status legend.
- Enforce the "every document has Purpose, Scope, Responsibilities, References, Status" rule.

## Status Legend

| Status | Meaning |
|---|---|
| Draft | Initial authoring; not yet approved |
| Active | Approved; is the current source of truth |
| Stale | Superseded by newer information; needs review |
| Superseded | Replaced by another document |

## Document List

### Reference (change rarely)

| Doc | Content |
|---|---|
| `reference/00_PROJECT_OVERVIEW.md` | Context, goals, domain terms, current status |
| `reference/02_SYSTEM_ARCHITECTURE.md` | Architecture, data flows, folder map, layer rules |
| `reference/04_DATABASE_SCHEMA.md` | Tables, data artifacts, staleness contracts |
| `reference/05_API_SPECIFICATION.md` | Canonical API contract |
| `reference/06_AI_PIPELINE.md` | Pipeline stages, weight/signal contracts |
| `reference/07_ANALYTICS_ENGINE.md` | Analytics engine catalog |
| `reference/14_AI_CONTEXT.md` | Compact AI context pack (domain + integrity) |

### Governance (change frequently)

| Doc | Content |
|---|---|
| `governance/08_ROADMAP.md` | Living development plan with per-item status |
| `governance/10_TECHNICAL_DEBT.md` | Living debt register |
| `governance/11_CODING_STANDARDS.md` | Conventions, commit/PR rules |
| `governance/12_TESTING_STRATEGY.md` | Test pyramid, evaluation gates |
| `governance/15_DEFINITION_OF_DONE.md` | Acceptance checklist for every change |
| `governance/16_CHANGELOG.md` | Chronological change history |
| `governance/17_PROJECT_RULES.md` | Universal engineering and process rules |

## Removed / Merged Documents

The original numbering scheme proposed documents `01`, `03`, `09`, and `13`. They were deliberately consolidated to keep the set minimal:

| Original | Disposition |
|---|---|
| `01_BUSINESS_REQUIREMENTS.md` | Folded into `reference/00_PROJECT_OVERVIEW.md` (revisit only if formal requirements are needed) |
| `03_FOLDER_STRUCTURE.md` | Folded into `reference/02_SYSTEM_ARCHITECTURE.md` (folder map) |
| `09_DECISIONS.md` | Replaced by ADR files in `decisions/` (one file per decision) |
| `13_RELEASE_PLAN.md` | Folded into `governance/08_ROADMAP.md` milestones until the first release is near |

## Related Indexes

| Index | Content |
|---|---|
| `decisions/` | Architecture decision records (`0000-*`, `0001-*`) |
| `prompts/README.md` | AI workflow playbooks and routing matrix |
| `specs/README.md` | Feature blueprint areas and lifecycle |

## References

- `README.md` — project entry point
- `decisions/` — architecture decision records
- `prompts/README.md` — AI workflow index
- `specs/README.md` — feature spec index
- `reports/audit/01-executive-summary.md` — audit snapshot entry
