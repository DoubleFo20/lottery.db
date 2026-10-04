# ADR-0003 — Verified miss advisory with monitoring checkpoints

**Status: Accepted — 2026-10-05**

## Context

Manager displays hardcoded prize outcomes rather than evaluating logged predictions.
The owner requested automatic reset after correcting the advisory.

## Decision

Keep history immutable and introduce a shared browser-side evaluation module.
Start monitoring after draw 2026-10-01; reset the monitoring checkpoint on changed
weights or top/beam/window parameters, independently of historical performance.
Verify eligible pre-draw candidates against canonical draw history. Exact wins
reset the consecutive count; unknown draws prevent claiming a consecutive streak.
Use no-store monitoring fetches, honored by the service worker.

## Consequences

- Actual prediction history remains unchanged; reset does not imply a model win.
- Model-change checkpoints persist per browser, not as a shared server record.
- Explicit source-only model revisions cannot be detected from the current payload.

## Alternatives considered

- Set a new hardcoded count: rejected because it invents performance evidence.
- Erase historical losses: rejected because it corrupts evaluation history.
- Reset on every refresh: rejected because alerts could never accumulate.

## References

- specs/frontend/04-miss-advisory-reset.md
- docs/reference/MISS_ADVISORY.md
- assets/miss_advisory.js
