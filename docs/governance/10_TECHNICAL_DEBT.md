# 10 — Technical Debt

**Status: Draft**

## Purpose

Maintains the living register of technical debt. Seeded from `reports/audit/08-technical-debt.md`; debt items are resolved through the roadmap and tracked here.

## Scope

- All known debt items (IDs D1–D24).
- Priority and remediation status per item.
- Linkage to roadmap phases.

## Responsibilities

- Keep item status current as debt is paid down.
- Add new debt items as discovered (e.g., by `prompts/audit.md`).
- Never delete an item; mark it Resolved with a reference to the change.

## Debt Register

### Critical

| ID | Debt | Roadmap |
|---|---|---|
| D1 | Self-learning weights never consumed by predictor | Phase 1 (R4) |
| D2 | Backtest uses random predictions + broken formula | Phase 1 (R6) |
| D3 | Fabricated actual results in prediction history | Phase 0 (R1) |
| D4 | Feature/temporal datasets stale by 8 draws | Phase 0 (R2) |

### High

| ID | Debt | Roadmap |
|---|---|---|
| D5 | Duplicate API layers, three dashboard paths | Phase 2 (R9) |
| D6 | Empty/broken API files | Phase 2 (R10) |
| D7 | Reversed transition matrix | Phase 1 (R5) |
| D8 | Two divergent prediction logs | Phase 2 (R11) |
| D9 | Duplicate scraper parsers | Phase 2 (R12) |
| D10 | Non-functional pipeline pattern step | Phase 1 (R7) |

### Medium

| ID | Debt | Roadmap |
|---|---|---|
| D11 | Uncalibrated confidence | Phase 3 (R16) |
| D12 | XAI recomputes factors | Phase 3 (R17) |
| D13 | Hardcoded credentials in two files | Phase 3 (R19) |
| D14 | Dashboard XAI schema mismatch | Phase 3 (R18) |
| D15 | Unescaped innerHTML | Phase 3 (R18) |
| D16 | Synchronous shell_exec architecture | Phase 3 (R20) |
| D17 | Open CORS, no auth | Phase 3 (R19) |
| D18 | Divergent cache/output schemas | Phase 2 (R13) |
| D19 | Zero test coverage | Phase 4 (R21) |

### Low

| ID | Debt | Roadmap |
|---|---|---|
| D20 | Empty scaffolding (11 dirs, 6 empty files) | Phase 2 (R14) |
| D21 | Empty i18n files | Phase 2 (R14) |
| D22 | Orphaned candidate generator | Phase 4 (R23) |
| D23 | No requirements.txt / README | Phase 2 (R15) |
| D24 | Broken/unusable git metadata | Phase 5 (R26) |

## References

- `docs/reference/02_SYSTEM_ARCHITECTURE.md` — layer rules driving consolidation
- `docs/governance/08_ROADMAP.md` — remediation phases
- `docs/reference/05_API_SPECIFICATION.md` — API debt detail (D5, D6, D17)
- `docs/reference/06_AI_PIPELINE.md` — AI-related debt detail
- `decisions/0001-target-source-layout.md` — target layout (D20)
- `reports/audit/08-technical-debt.md` — audit snapshot
