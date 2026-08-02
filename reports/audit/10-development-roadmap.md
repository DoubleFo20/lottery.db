# 10. Development Roadmap

**Document type:** Audit report (documentation only)
**Project:** Lottery analysis suite
**Root:** `D:\xampp\htdocs\Lottery`

Purpose: an ordered, evidence-based remediation plan derived from the audit. This document describes **what** should be done and **why**; it does not contain code and no changes were made.

---

## 10.1 Guiding Principles

1. **Restore ground truth first.** No metric, dashboard, or model improvement is meaningful until actuals are correct and datasets are current.
2. **Close the self-learning loop.** The system's signature feature must actually affect predictions.
3. **Make validation honest.** Everything reported must come from real, walk-forward evaluations.
4. **Consolidate before extending.** Delete duplication and dead code before adding features.
5. **Verify continuously.** Add tests and measurable baselines as each phase lands.

## 10.2 Phase 0 — Data Integrity (Critical)

| Step | Action | Evidence / reason |
|---|---|---|
| R1 | Replace the fabricated `"123456"` actuals with real draw results (`292514` for `2026-04-01`); audit the whole `prediction_history.csv`/`.json` for other corrupt entries | `reports/audit/05-analytics-audit.md` §5.3 |
| R2 | Regenerate `lottery_features.csv` and `lottery_temporal_features.csv` to match 467 history rows (through `2026-07-01`); diagnose why the scheduler trigger (`update_scheduler.py:382-396`) stopped at `2026-03-01` | §5.4 |
| R3 | Re-derive root `performance.json`, `analytics/accuracy_report.json`, and `analytics/model_adjustments.json` from corrected actuals | §5.3 |

**Exit criteria:** all recorded metrics trace to real draw results; feature datasets match the master history.

## 10.3 Phase 1 — Core Correctness (Critical)

| Step | Action | Evidence / reason |
|---|---|---|
| R4 | Make the predictor load `database/predictions/ensemble_weights.json` (validate keys/sums; fall back to defaults) | `reports/audit/06-ai-audit.md` §6.2 |
| R5 | Reverse the transition matrix: build it from chronologically **ascending** rows so it encodes `P(next_draw|current_draw)` | §6.4 |
| R6 | Fix the backtest: drive it with the real predictor, split by walk-forward windows, and correct the accuracy formula to `(total_pos_hits / (6 * total_draws)) * 100` | §5.2 |
| R7 | Implement the pipeline "pattern" step via the real `analytics/pattern_engine.py`, or remove the stub | §5.5 |
| R8 | Add a measured random-baseline comparison (replace the hardcoded constant in `self_learning_manager.py:214-221`) | §6.8 |

**Exit criteria:** self-learning changes predictions; backtest reflects model behavior; transition signal is correct.

## 10.4 Phase 2 — Consolidation & Architecture (High)

| Step | Action | Evidence / reason |
|---|---|---|
| R9 | Consolidate to a single PHP API layer; standardize dashboards on one base URL | `reports/audit/07-frontend-audit.md` §7.2 |
| R10 | Delete zero-byte files (`backend/api/history.php`, `backend/api/statistics.php`, `database/api/history.php`, `database/api/statistics.php`) and the broken `database/api/predict.php` (or fix its include) | §8.2 D6 |
| R11 | Merge the two prediction logs (`prediction_history.json` vs `prediction_log.json`) into one schema | `06-ai-audit.md` §6.3 |
| R12 | Remove duplicate `parse_thairath_page` (`lottery_scraper.py:190` and `:403`) and consolidate scraper parsers | §8.2 D9 |
| R13 | Align `pipeline_cache.json` and `pipeline_output.json` schemas; delete the orphaned output | §8.3 D18 |
| R14 | Decide on `frontend/`: implement it or remove the empty scaffolding; likewise `dashboard/components`, `dashboard/charts` | §8.4 D20 |
| R15 | Add `requirements.txt` (pin installed versions) and a README | §8.4 D23 |

**Exit criteria:** one API path, one log, one parser, no zero-byte files, reproducible environment.

## 10.5 Phase 3 — Quality, Calibration & Security (Medium-High)

| Step | Action | Evidence / reason |
|---|---|---|
| R16 | Calibrate confidence (e.g., histogram calibration over walk-forward folds) or relabel as relative rank | §6.5 |
| R17 | Make XAI read the predictor's actual per-signal contributions instead of recomputing factors | §6.6 |
| R18 | Escape all dynamically inserted values in dashboards (prefer `textContent`); fix the XAI schema mismatch in `app.js:149` | §7.3–7.4 |
| R19 | Add authentication and origin allow-listing; move credentials to environment variables | §4.4 |
| R20 | Replace `shell_exec` with a persistent worker/service that pre-writes JSON caches | §4.5 |

**Exit criteria:** confidence is honest; explanations match the model; dashboards escape content; endpoints are authenticated; no process-per-request execution.

## 10.6 Phase 4 — Testing, Integration & ML (Medium)

| Step | Action | Evidence / reason |
|---|---|---|
| R21 | Add pytest coverage for engines, backtest, and PHP API contracts; add fixtures with known datasets | §8.3 D19 |
| R22 | Wire `trend_scanner` signals into the ensemble as weighted inputs, or remove them from the cache | §6.7 |
| R23 | Either integrate `candidate_generator.py` into the pipeline or delete it | §6.7 |
| R24 | Introduce walk-forward evaluation as a permanent regression gate | §6.8 |
| R25 | (Optional) After validation infrastructure exists, add real ML (e.g., calibrated classifiers on engineered features) using the already-installed scikit-learn | §6.8 |

**Exit criteria:** full test suite green; trend/candidate signals either integrated or removed; every prediction change is validated walk-forward.

## 10.7 Phase 5 — Process & Governance (Low)

| Step | Action | Evidence / reason |
|---|---|---|
| R26 | Re-initialize Git properly and commit the corrected baseline | §8.4 D24 |
| R27 | Add the walk-forward baseline and accuracy gates to any CI | §6.8 |
| R28 | Publish the corrected `summary_report.md` and update `reports/` to match reality | §5.3 |

## 10.8 Sequencing and Dependencies

```
Phase 0 (Data Integrity)  ── must precede everything
   │
   ▼
Phase 1 (Core Correctness) ── needs corrected data; unlocks honest metrics
   │
   ▼
Phase 2 (Consolidation)   ── needs stable engines; unlocks maintainable UI/API
   │
   ▼
Phase 3 (Quality/Security) ── independent; can partially overlap Phase 2
   │
   ▼
Phase 4 (Testing/ML)      ── needs stable, consolidated code
   │
   ▼
Phase 5 (Process)         ── continuous
```

**Note on overlap:** Phases 3 (security: R18–R20) and 5 (R26) can start in parallel with Phase 2 because they touch distinct files. Phases 0 and 1 must complete before any metric-based decisions are made.

## 10.9 Expected Outcomes After Full Implementation

| Metric | Today (audited) | Target after roadmap |
|---|---|---|
| Reported model scores | Derived from fabricated actuals | Walk-forward, real-actuals baseline |
| Self-learning effect | None (weights never read) | Weights consumed; measurable adaptation |
| Backtest validity | Random numbers + invalid formula | Real model, correct formula |
| Feature data freshness | 459/467 draws | Synced to master history |
| Test coverage | 0 files | Engine + API test suite |
| API paths | 3 divergent | 1 canonical path |
| Confidence honesty | Top candidate 100% | Calibrated or labeled relative |
| Reproducibility | No requirements.txt | Pinned dependencies + README |

## 10.10 Closing

This roadmap is documentation only. It is derived from evidence cited throughout the audit set (`reports/audit/01`–`09`) and should be re-validated before each phase begins. Implementation is a separate task requiring explicit approval.
