# Scroll canvas idle rendering

**Status: Implemented — 2026-10-05**

## Purpose

Stop repeated fallback drawing and perpetual animation callbacks after scroll
interpolation settles. Cover the React demo and both standalone demos in a browser.

## Scope

- In scope: StickyScrollCanvas.tsx, scroll-canvas.html, video-generator/index.html,
  canvas harnesses, test dependency, dedicated browser CI and supporting documentation.
- Out of scope: legacy 3d.html animation behavior, prediction data, deployment configuration.
- Approval: owner requested implementation and GitHub push in this conversation.

## Inputs

Scroll position, motion preference, canvas dimensions and decoded image availability.

## Outputs

On-demand rendering that wakes for scroll, resize, motion change and decoded images,
and suspends while hidden. No public prop or image-path contract changes.

## Acceptance Criteria

- Missing target and all-missing frames settle with zero pending/executed rAF
  callbacks and zero canvas draws during a browser idle measurement.
- Healthy scrolling selects the correct frames; resize repaints.
- Delayed images replace the fallback after the scheduler has gone idle.
- Reduced-motion mode settles, and unmount/effect replay cancels old work.
- Demo discovery does not silently omit the Next root or standalone demos.
- Preserve the legacy regression harness as a separate command.
- Run the new browser checks on changes to the demos and harness.

## Dependencies

ADR-0002; puppeteer-core with an installed Chrome/Chromium; Next production server.

## References

- decisions/0002-scroll-canvas-on-demand.md
- docs/reference/SCROLL_CANVAS.md
- next-app/src/components/StickyScrollCanvas.tsx
- scripts/stress-3d-canvas.js
- scripts/test-canvas-lifecycle.js
