# AGENTS.md — AI Operating Manual

**Status: Draft**

## Purpose

Defines how AI assistants (DeepSeek, Gemini, Claude, GPT, and tool-embedded agents) operate in this repository. It ensures every AI run follows the same conventions, reads the correct context, and obeys the same guardrails.

## Scope

Applies to all AI-assisted work: planning, specification, implementation, refactoring, testing, review, debugging, and auditing. Does not override human approval gates.

## Responsibilities

- Establish the mandatory pre-task context reads.
- Define universal guardrails for all AI work.
- Provide the task-to-model routing matrix.
- Link to the detailed prompt playbooks.

## Mandatory Pre-Task Context

Before starting any task, read:

1. `AI_RULES.md` — non-negotiable rules of engagement.
2. `docs/reference/14_AI_CONTEXT.md` — compact domain and integrity context.
3. `README.md` — project entry point.
4. `docs/governance/11_CODING_STANDARDS.md` — code conventions.
5. The relevant reference doc for the area being touched:
   - Data: `docs/reference/04_DATABASE_SCHEMA.md`
   - API: `docs/reference/05_API_SPECIFICATION.md`
   - AI/prediction: `docs/reference/06_AI_PIPELINE.md`
   - Analytics: `docs/reference/07_ANALYTICS_ENGINE.md`
6. `reports/audit/01-executive-summary.md` — known integrity defects (unless a newer audit supersedes it).

## Universal Guardrails

1. **Evidence rule.** Cite `file:line` for every claim. State "Not enough evidence" when something cannot be verified from the repository. Never guess.
2. **Read-only modes.** `audit` and `review` tasks never modify the repository.
3. **Scoped writes.** `build`, `refactor`, and `test` tasks write only within the approved spec's scope and never touch files outside it.
4. **Verification.** Every write ends with verification (lint, tests, or a dry-run) plus human sign-off against `docs/governance/15_DEFINITION_OF_DONE.md`. No verification, no merge.
5. **No secrets.** Never commit credentials, API keys, or tokens. Never log secrets.
6. **No source mutation during documentation work.** Documentation tasks do not modify application source code, databases, APIs, or frontend components.
7. **Doc hygiene.** When modifying a document, update its `Status` and `References` sections.
8. **Follow standards.** Adhere to `docs/governance/11_CODING_STANDARDS.md` and `docs/governance/12_TESTING_STRATEGY.md`.

## Model Routing Matrix

Prompts are model-agnostic. The operator selects the model per the matrix in `prompts/README.md`. Capabilities change; update the matrix in `prompts/README.md` when a model's strengths shift.

| Task | Prompt | Preferred model |
|---|---|---|
| Planning / roadmap | `prompts/roadmap.md` | Claude |
| Architecture & security review | `prompts/audit.md`, `prompts/review.md` | Claude |
| Repository synthesis / summaries | `prompts/roadmap.md` | Gemini |
| Spec authoring | `prompts/spec.md` | Claude or GPT |
| Bulk code generation / large refactor | `prompts/build.md`, `prompts/refactor.md` | DeepSeek |
| General implementation & tests | `prompts/build.md`, `prompts/test.md` | GPT |
| Debugging / root cause analysis | `prompts/debug.md` | Claude or GPT |

## References

- `AI_RULES.md` — non-negotiable rules of engagement
- `docs/reference/14_AI_CONTEXT.md` — domain and integrity context
- `prompts/README.md` — routing matrix and workflow
- `docs/governance/11_CODING_STANDARDS.md` — coding conventions
- `docs/governance/12_TESTING_STRATEGY.md` — testing standards
- `docs/governance/15_DEFINITION_OF_DONE.md` — acceptance checklist
- `docs/governance/17_PROJECT_RULES.md` — project rules
- `reports/audit/01-executive-summary.md` — known defects
