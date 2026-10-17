# TASKS.md — Mission-Critical Workplan & Progress

**Feature Branch:** `feat/mission-critical-remediation`  
**Pull Request:** PR #1 (Draft) — https://github.com/DoubleFo20/lottery.db/pull/1  
**Status:** PR #1 Review Remediation Complete & Verified  
**Lead Orchestrator:** ARGON

---

## Phase A: Merge Conflict Resolution with `origin/main`
- [x] Fetch `origin/main` (`c62352d`) containing automated GitHub Actions cron commits.
- [x] Merge `origin/main` into `feat/mission-critical-remediation`.
- [x] Resolve conflict in `database/dataset/lottery_history.csv` preserving canonical 473-draw history (latest draw `2026-10-16`: `011781`, `48`, `402, 392`, `171, 255`).
- [x] Resolve conflict in `performance.json` preserving honest deduplicated ground truth (`evaluated: 2`, `avg_pos_hits: 1.00/6`).
- [x] Regenerate `database/predictions/pipeline_cache.json` via `python api/run_pipeline.py`.
- [x] Rebuild `hopper_3d_data.json` across both locations via `npm run build`.
- [x] Commit merge resolving all conflicts cleanly (Commit `48008b3`).

## Phase B: Independent Review Findings Remediation
- [x] Implement look-ahead data leakage audit `audit_weights_leakage()` in `analytics/backtest_engine.py` (CLI: `--audit`).
- [x] Enforce strict chronological pre-draw history assertion in walk-forward evaluation (`assert all(h["draw_date"] < draw_date for h in history_up_to)`).
- [x] Support untuned a-priori equal weights mode (`--weights equal`) in `EnsemblePredictor` and `run_backtest()`.
- [x] Implement official GLO prize structure in `score_prediction()` and `run_backtest()`: First Prize Jackpot, Front-3 (`front3_1`, `front3_2`), Back-3 (`back3_1`, `back3_2`), Last-2 (`actual_last2`), Top-2, Top-3 Direct, and Top-3 Box.
- [x] Implement draw-level statistical uncertainty evaluation ($\bar{X}_{pos}$, $s_{pos}$, $SE_{draw}$, 95% CI, and draw-level hypothesis test vs null 0.60 hits/draw).
- [x] Report prediction success coverage metrics (`coverage_rate_pct`, `attempted_draws`, `successful_draws`, `prediction_failures`, `failure_rate_pct`).
- [x] Zero random fallback strictly maintained: predictor failures are recorded explicitly and never masked with random numbers.

## Phase C: Verification Suite
- [x] Python regression suite: **235 / 235 passed** (`pytest tests/`).
- [x] Leakage audit verified: **PASSED** (`python analytics/backtest_engine.py --audit`).
- [x] Node.js test & 3D data prep: **PASSED** (`npm test`).
- [x] Advisory regression suite & Puppeteer browser test: **PASS** (`npm run test:advisory`).
- [x] Canvas lifecycle test: **PASS** (`npm run test:canvas:lifecycle`).
- [x] 3D assets build: **Clean** (`npm run build`).
- [x] Re-run comparative backtest with draw-level stats: **PASSED** (`comparative_report.json` updated).

## Phase D: CI Repair & Merge Readiness
- [x] Fix TypeScript `LayoutProps` error in `next-app/src/app/layout.tsx` using `Readonly<{ children: ReactNode }>`.
- [x] Verify `npx tsc --noEmit --incremental false` passes with 0 errors on clean checkout.
- [x] Verify `npm run lint` and `npm run build` pass in `next-app`.
- [x] Isolate backtest weights by defaulting comparative backtest to untuned equal weights (`weights_mode="equal"`).
- [x] Clearly distinguish official GLO equipment prizes from independent market sub-combination models.
- [x] Run full regression tests (235 passed in Pytest, advisory tests, canvas lifecycle, legacy stress).
- [x] Update `HANDOFF.md`, `PROJECT_STATUS.md`, and `TASKS.md`.
- [ ] Commit and push verified fixes to `origin/feat/mission-critical-remediation`.
- [ ] Verify GitHub Actions workflows complete with green status on PR #1.
- [ ] Keep PR #1 in Draft status for owner review.

