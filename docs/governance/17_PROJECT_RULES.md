# 17 — Project Rules

**Status: Draft**

## Purpose

Defines the universal engineering and process rules that apply to everyone working in this repository — humans and AI assistants alike. This document focuses on how the project is run; `AI_RULES.md` operationalizes the same values as behavioral rules for AI sessions.

## Scope

- Process and workflow rules: specs, architecture, testing, documentation, compatibility, metrics, and communication.
- Complements, does not duplicate, `AI_RULES.md`.

## Responsibilities

- State the rules all contributors follow.
- Serve as the source that `docs/governance/15_DEFINITION_OF_DONE.md` and `AI_RULES.md` reference.
- Be updated only through the governance workflow (roadmap/ADR), not ad hoc.

## Rules

1. **Spec-first.** No implementation without an approved spec under `specs/` (see `prompts/spec.md`).
2. **Architecture by approval.** Any architectural change requires an ADR in `decisions/` before implementation.
3. **Tests gate merges.** Nothing merges without tests per `docs/governance/12_TESTING_STRATEGY.md`.
4. **Docs move with code.** Every code change updates the affected documentation and its status.
5. **Backward compatibility.** Public contracts (API, log schemas, cache schemas) change only with an ADR and a deprecation path.
6. **Honest metrics.** All performance numbers derive from real draw results; fabricated actuals are a critical defect (D3).
7. **Evidence over guessing.** Cite `file:line`; when uncertain, ask.
8. **Changelog discipline.** Notable changes are appended to `docs/governance/16_CHANGELOG.md`.
9. **Audit immutability.** `reports/audit/` is read-only; living versions live in `docs/`.
10. **Repo hygiene.** No secrets; no generated artifacts committed; git metadata must be re-initialized (Phase 5, R26).

## Relationship to AI_RULES.md

`AI_RULES.md` translates these project rules into eight non-negotiable behavioral rules for AI assistants. Where a conflict appears, `AI_RULES.md` is binding for AI work.

## References

- `AI_RULES.md` — AI behavioral rules
- `docs/governance/15_DEFINITION_OF_DONE.md` — acceptance checklist
- `docs/governance/11_CODING_STANDARDS.md` — conventions
- `docs/governance/08_ROADMAP.md` — approved work
- `docs/governance/16_CHANGELOG.md` — change history
