# Prompts — Routing Matrix & Workflow

**Status: Draft**

## Purpose

Indexes the AI workflow playbooks in `prompts/` and provides the task-to-prompt-to-model routing matrix. This is the operational reference for all AI-assisted development.

## Scope

- All prompt playbooks and when to use them.
- Model routing with rationale.
- The development workflow loop.

## Responsibilities

- Keep the routing matrix in `AGENTS.md` current as model capabilities change (this file links to it rather than duplicating it).
- Define inputs/outputs/guardrails expectations for each prompt.
- Link each prompt to the documents it consumes and produces.

## Prompt Index

| Prompt | Use when | Primary consumer |
|---|---|---|
| `audit.md` | Periodic evidence-based review | Read-only snapshot + debt updates |
| `spec.md` | Turning an idea into a feature blueprint | Writes to `specs/` |
| `build.md` | Implementing an approved spec | Writes code within spec scope |
| `refactor.md` | Restructuring existing code | Guided by ADRs and tests |
| `test.md` | Adding test coverage | Writes tests per testing strategy |
| `review.md` | Reviewing a diff/PR | Read-only review |
| `debug.md` | Root-cause analysis | Evidence-first diagnosis |
| `roadmap.md` | Planning phases and priorities | Updates roadmap + ADRs |

## Model Routing Matrix

Prompts are model-agnostic; the operator selects the model. The canonical routing matrix (task → prompt → preferred model) lives in `AGENTS.md` to keep a single source of truth and avoid drift.

| Task | Prompt | Preferred model |
|---|---|---|
| Planning / roadmap | `roadmap.md` | Claude |
| Architecture & security review | `audit.md`, `review.md` | Claude |
| Repository synthesis / summaries | `roadmap.md` | Gemini |
| Spec authoring | `spec.md` | Claude or GPT |
| Bulk code generation / large refactor | `build.md`, `refactor.md` | DeepSeek |
| General implementation & tests | `build.md`, `test.md` | GPT |
| Debugging / root cause analysis | `debug.md` | Claude or GPT |

> Note: this table mirrors the canonical matrix in `AGENTS.md`. Update `AGENTS.md` first, then mirror here.

## Workflow Loop

```
roadmap.md → docs/08 + ADRs + backlog
spec.md    → specs/<area>/<feature>.md
build.md   → implementation vs spec + docs/11
test.md    → tests per docs/12
review.md  → diff vs spec, standards, API contract
[human gate: approve/merge]
audit.md   → periodic; updates reports/ + docs/10 + docs/08
```

## Shared Guardrails

1. Evidence rule: cite `file:line`; "Not enough evidence" when unsure.
2. `audit`/`review` are read-only.
3. `build`/`refactor`/`test` write only within approved spec scope.
4. Every write ends with verification plus human sign-off.
5. No secrets; follow `docs/governance/11_CODING_STANDARDS.md`.

## References

- `AGENTS.md` — operating manual, guardrails, and canonical routing matrix
- `docs/governance/08_ROADMAP.md` — roadmap the workflow drives
- `specs/README.md` — spec areas the workflow produces
- `docs/README.md` — document map
