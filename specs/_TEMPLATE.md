# Spec Template

**Status: Draft**

## Purpose

Standard structure for feature blueprints in `specs/<area>/`. Every spec follows this template so it can be implemented (`prompts/build.md`) and reviewed (`prompts/review.md`) consistently.

## Scope

- Copy this file into `specs/<area>/<feature>.md`.
- Fill each section; keep it concise and evidence-based.
- Do not include implementation code.

## Spec Fields

```markdown
# <Feature Title>

Status: Draft | Approved | Implemented | Superseded

## Purpose
What problem this spec solves and why.

## Scope
- In scope:
- Out of scope:
- Areas affected: analytics / ai / backend / frontend / database

## Inputs
Data and contracts this feature consumes (files, artifacts, references).

## Outputs
What this feature produces (artifacts, behavior, API surface).

## Acceptance Criteria
Checkable statements that define "done".

## Dependencies
Roadmap items, debt IDs, ADRs, other specs.

## References
- Related documents, prompts, and specs.
```

## References

- `specs/README.md` — lifecycle and area conventions
- `prompts/spec.md` — how to write specs
- `prompts/build.md` — how specs are implemented
- `AGENTS.md` — guardrails
