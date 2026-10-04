# Automatic consecutive miss advisory reset

**Status: Implemented — 2026-10-05**

## Purpose

Replace hardcoded miss/win counts in Manager with verified draw monitoring and
automatically start a new tracking cycle after the requested correction.

## Scope

Root and dashboard Manager pages, shared advisory script and mirror, service-worker freshness, targeted tests,
and supporting documentation. No model tuning, prediction-log mutation or data deletion.
Owner requested automatic reset after the fix in this conversation.

## Inputs

Canonical lottery_history.csv, prediction_history.json, active ensemble weights
and top/beam/window parameters from the prediction payload.

## Outputs

A monitoring checkpoint after draw 2026-10-01, independent of historical performance.
Persist a model configuration fingerprint in localStorage; changed weights or
parameters automatically start a new cycle after the latest completed draw.
Exact first-prize hits reset the consecutive miss count naturally.

## Acceptance Criteria

- No fabricated six-draw, three-draw or 4/6 success metrics.
- Count each verified, pre-draw prediction once per actual draw.
- Unknown/late/mismatched results cannot establish a consecutive streak.
- Refreshing predictions without configuration changes does not reset.
- New model configuration resets; repeated refreshes preserve the checkpoint.
- Insufficient data displays waiting/unknown, not a high alert or a claimed win.
- Both Manager pages remain identical and load the shared logic.

## Dependencies

Existing prediction/history contracts; localStorage optional with policy fallback.

## References

- assets/miss_advisory.js
- manager.html
- dashboard/manager.html
- scripts/test-miss-advisory.js
- docs/reference/MISS_ADVISORY.md
- docs/reference/04_DATABASE_SCHEMA.md
- decisions/0003-miss-advisory-checkpoint.md
