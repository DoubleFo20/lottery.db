# Consecutive draw miss advisory

**Status: Implemented — 2026-10-05**

## Monitoring

The old Manager banner used literal counts of six misses, three two-digit misses
and four banker wins. Those values are removed. The current tracking cycle begins
after draw 2026-10-01 following the owner's reset request. This is a monitoring
checkpoint, not a claim that the prediction model won or its accuracy improved.
Historical logs and actual draw data remain intact.

The shared script fingerprints ensemble weights and top/beam/window parameters.
It persists the fingerprint/checkpoint in localStorage. When this configuration
changes, the browser automatically starts a new cycle after the latest known actual
draw. Timestamps, candidate changes and repeated refreshes do not trigger resets.
Without accessible storage, tracking uses the shared initial policy checkpoint.
Checkpoints are per browser; a new client begins at the shared policy date.
Advisory/history and model-cache requests use no-store, which the service worker
honors by fetching directly. The cache version changes to expire old Manager HTML.

## Evidence

Only predictions logged before 14:30 Asia/Bangkok on the target date, with a
historical input date before that target and valid six-digit candidates, are
eligible. Naive Python log timestamps are interpreted as Asia/Bangkok.
Stored actuals must match canonical history if present. The latest eligible run
per draw is selected, so rerunning predictions does not count an extra draw.

Exact six-digit hits reset the streak. Unknown intervening draws break evidence of
consecutiveness and show insufficient data. Pending draws and data loading failures
do not count as misses. The alert threshold remains selectable from 3 to 6 draws.
Two-digit and Banker metrics show unavailable until historical predictions for
those prizes have a verified evaluation contract.

Model source changes without changed weights/parameters are not detectable from
the current payload. A future explicit model revision can extend the fingerprint.

Verified locally on 2026-10-05: 13 advisory behavior tests, both actual Manager pages
in Chrome, five Manager pytest checks, JavaScript/HTML syntax checks, workflow YAML
parsing and git diff --check. Historical result files were not modified.

## Verification

- node --test scripts/test-miss-advisory.js
- python -m pytest tests/test_manager_dashboard.py
- Browser smoke checks of both Manager paths and live recalculation.
- node scripts/test-manager-advisory-browser.js executes both actual pages, verifies
  initial reset, six verified misses, an exact win, model-change reset and persistence.

## References

- specs/frontend/04-miss-advisory-reset.md
- assets/miss_advisory.js
- dashboard/assets/miss_advisory.js
- scripts/test-miss-advisory.js
- tests/test_manager_dashboard.py
- scripts/test-manager-advisory-browser.js
- sw.js
- decisions/0003-miss-advisory-checkpoint.md
- .github/workflows/manager_advisory_regression.yml
