# AI_RULES.md — AI Rules of Engagement

**Status: Draft**

## Purpose

Defines non-negotiable rules every AI assistant must follow when working in this repository. These rules sit above task-specific guardrails and cannot be overridden by a single prompt.

## Scope

Applies to all AI-assisted work: planning, specification, implementation, refactoring, testing, review, debugging, and auditing. Does not override human approval gates.

## Responsibilities

- Govern all AI behavior in the repository.
- Provide the operator with a simple pass/fail checklist for AI output.
- Link each rule to the Project OS documents that operationalize it.

## Rules

1. **Never invent features.** Do not add behavior that is not present in an approved spec or roadmap item. New ideas are written as specs under `specs/` via `prompts/spec.md` before any implementation.
2. **Never modify architecture without approval.** Architectural changes require an Architecture Decision Record (`decisions/`) and approval before implementation (see `docs/reference/02_SYSTEM_ARCHITECTURE.md`).
3. **Every implementation must reference a spec.** `prompts/build.md` writes code only against an approved spec under `specs/`; `prompts/review.md` verifies the linkage.
4. **No feature without tests.** New behavior requires tests per `docs/governance/12_TESTING_STRATEGY.md` before it is considered done.
5. **No code without documentation.** Code changes update the affected documentation (status and references) per `AGENTS.md` doc hygiene, and reflect new behavior in the reference docs.
6. **Always preserve backward compatibility.** Public contracts — API surface (`docs/reference/05_API_SPECIFICATION.md`), prediction-log schema, and cache schema — must not break without an ADR and a deprecation path.
7. **Never fabricate performance metrics.** Metrics must derive from real draw results in `database/dataset/lottery_history.csv`. Fabricated actuals (see `docs/governance/10_TECHNICAL_DEBT.md` D3) are a critical integrity defect and invalidate all downstream metrics.
8. **If uncertain, ask instead of guessing.** Follow the evidence rule: cite `file:line`, state "Not enough evidence" when something cannot be verified, and ask the operator when intent is ambiguous.

## References

- `AGENTS.md` — operating manual and guardrails (must be read with this file)
- `prompts/README.md` — workflow playbooks and routing matrix
- `docs/governance/17_PROJECT_RULES.md` — universal project rules
- `docs/governance/15_DEFINITION_OF_DONE.md` — acceptance checklist
- `docs/governance/11_CODING_STANDARDS.md` — conventions
- `docs/governance/12_TESTING_STRATEGY.md` — verification standards
- `docs/governance/08_ROADMAP.md` — approved work
- `docs/governance/10_TECHNICAL_DEBT.md` — known integrity defects
