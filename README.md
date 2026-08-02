# Lottery — Project Operating System

**Status: Draft**

## Purpose

This repository hosts a Thai-state-lottery analysis and prediction suite. The Project Operating System (Project OS) is the set of documents, prompts, and specifications that govern long-term development. Its purpose is to keep every human and AI contributor aligned on architecture, conventions, and workflow.

## Scope

- Covers the entire repository: analytics engines, ensemble prediction, self-learning, scraping, PHP API layer, dashboards, and data artifacts.
- Includes the Project OS itself (this file, `docs/`, `decisions/`, `prompts/`, `specs/`).
- Excludes runtime operations (deployment, scheduler health) until documented in `docs/reference/OPERATIONS.md`.

## Responsibilities

- **This file** is the entry point: it explains what the project is and points to the correct documents.
- **`AI_RULES.md`** defines non-negotiable rules for AI work (never invent features, no code without tests/docs, etc.).
- **`AGENTS.md`** defines how AI assistants operate in this repository (conventions, model routing, guardrails).
- **`docs/`** holds the living reference and governance documentation.
- **`decisions/`** holds Architecture Decision Records (ADRs).
- **`prompts/`** holds reusable AI workflow playbooks.
- **`specs/`** holds feature blueprints that drive implementation.
- **`reports/audit/`** holds the immutable audit snapshot (read-only).

## Quickstart

1. Read `docs/reference/00_PROJECT_OVERVIEW.md` for context.
2. Read `docs/reference/02_SYSTEM_ARCHITECTURE.md` for how the system is structured.
3. Read `docs/governance/11_CODING_STANDARDS.md` before writing code.
4. Follow the workflow in `prompts/README.md` for AI-assisted tasks.

## References

- `AI_RULES.md` — AI rules of engagement
- `AGENTS.md` — AI operating manual
- `docs/README.md` — document map and status legend
- `docs/reference/00_PROJECT_OVERVIEW.md` — project context
- `docs/reference/02_SYSTEM_ARCHITECTURE.md` — architecture
- `reports/audit/01-executive-summary.md` — audit snapshot
