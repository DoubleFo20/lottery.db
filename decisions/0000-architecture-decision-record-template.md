# ADR-0000 — Architecture Decision Record Template

**Status: Draft**

## Purpose

Provides the standard structure for Architecture Decision Records (ADRs) in `decisions/`. Every major design decision is recorded as one file so decisions are diffable, referenceable, and reversible.

## Scope

- Format for new ADRs.
- Numbering and lifecycle.
- Relationship to `docs/` and `specs/`.

## Responsibilities

- Maintain the numbering sequence (`0000`, `0001`, ...).
- Enforce that every ADR follows this template.
- Link each ADR to the roadmap item and affected documents.

## Template

```markdown
# ADR-NNNN — <Title>

Status: Draft | Accepted | Superseded (by ADR-XXXX)

## Context
Why this decision is needed.

## Decision
What was decided.

## Consequences
- Positive:
- Negative:
- Risks:

## Alternatives considered
Brief list of rejected alternatives and why.

## References
- Related ADRs
- Roadmap item(s)
- Documents/specs affected
```

## Numbering

- Increment the sequence number for each new ADR.
- Never reuse a number; superseded ADRs stay on file.

## References

- `docs/reference/02_SYSTEM_ARCHITECTURE.md` — architecture this decides on
- `docs/governance/08_ROADMAP.md` — roadmap linkage
- `AGENTS.md` — AI operating rules for creating ADRs
