# Scroll canvas rendering and verification

**Status: Implemented — 2026-10-05**

## Rendering

The React and standalone scroll-sequence demos use Canvas 2D, not WebGL.
They keep at most one pending animation callback. Interpolation stops at its
target, independent of image success. The selected decoded image (or placeholder)
is painted only when its identity or canvas dimensions change.

Scroll, resize, motion preference changes and image completion wake rendering.
Hidden documents suspend callbacks. React cleanup disables wakeups and cancels
pending work; image callbacks retain cancellation guards across decoding.

## Verification

Install root dependencies with npm ci. Install Next dependencies separately.
Build and start next-app in production, then set NEXT_BASE_URL to that server.

PowerShell example:

```powershell
$env:NEXT_BASE_URL = 'http://127.0.0.1:3000/'
npm run test:canvas
node scripts/test-canvas-lifecycle.js
npm run test:canvas:legacy
```

Set CHROME_PATH if Chrome/Chromium is not in a standard location. The harness
starts its own temporary static HTTP server. It discovers registered static demos
and concrete App Router pages, and fails on unmapped dynamic routes or unregistered
canvas routes. Register new scroll demos with data-canvas-benchmark="scroll-sequence".

Browser scenarios cover healthy, missing target, all missing and delayed target
images, with reduced motion enabled and disabled. They assert no idle rAF activity
or draws, correct healthy frames, delayed recovery and resize wakeup.
Images are deterministic synthetic fixtures, not a visual review of production assets.
TaskDuration deltas and heap usage are diagnostic metrics, not a 0% CPU/GPU claim.

The TSX lifecycle check executes the real transpiled source with controlled hooks
and browser dependencies. It covers unmount, late completion, effect replay and
visibility. It is not a substitute for browser hydration coverage.

Canvas Browser Regression runs these checks on relevant pushes and pull requests,
including a production Next build and Chrome browser execution on GitHub Actions.

## Verification record — 2026-10-05

- next-app: npm run lint, npx tsc --noEmit --incremental false and npm run build passed.
- npm run test:canvas: 24 production-browser scenarios passed across all three demos;
  every measured idle window had zero additional rAF callbacks and canvas draws.
- node scripts/test-canvas-lifecycle.js passed; legacy harness passed 12 checks.
- The same browser harness rejected the original scroll-canvas.html from cceb5ed
  at its idle check (pending rAF never reached zero), without changing source files.
- Standalone scripts passed syntax parsing; workflow YAML parsed; git diff --check passed.
- GitHub Actions execution is verified separately after pushing; local checks use
  synthetic image fixtures and do not establish whole-browser CPU/GPU utilization.

## References

- specs/frontend/03-scroll-canvas-idle.md
- decisions/0002-scroll-canvas-on-demand.md
- next-app/src/components/StickyScrollCanvas.tsx
- scripts/stress-3d-canvas.js
- scripts/test-canvas-lifecycle.js
- scripts/stress-3d-canvas-legacy.js
- .github/workflows/canvas_regression.yml
