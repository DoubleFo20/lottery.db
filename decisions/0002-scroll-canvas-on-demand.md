# ADR-0002 — Scroll canvas on-demand rendering

**Status: Accepted — 2026-10-05**

## Context

The current renderer compares requested frame identity to fallback identity and
always schedules another animation callback. The legacy Node VM harness truncates
callbacks and does not exercise new demos in a browser.

## Decision

Use at most one pending rAF, schedule only while interpolation is moving, and wake
on scroll, resize, motion change or decoded images. Deduplicate paints by selected
image identity; frame 0 represents the placeholder. Cancel on effect cleanup and
visibility suspension. Keep existing props, preloading sequence and image paths.

The owner authorized the proposed correction and GitHub push in the conversation
on 2026-10-05. Use Puppeteer browser failure injection for registered demos and a
controlled execution of actual TSX for React effect cleanup/replay.

## Consequences

- Positive: idle rendering consumes no application rAF callbacks or canvas draws.
- Negative: the browser test needs installed Chromium and a running Next server.
- Risks: page-wide rAF checks require isolated demos; task-time metrics do not
  establish whole-process CPU or GPU utilization.

## Alternatives considered

- Throttle the perpetual loop: retains unnecessary callbacks.
- Only compare requested frames: misses fallback upgrades and keeps rAF running.
- Remove the legacy tests: loses existing coverage, so retain them separately.

## References

- specs/frontend/03-scroll-canvas-idle.md
- docs/reference/SCROLL_CANVAS.md
- scripts/stress-3d-canvas-legacy.js
