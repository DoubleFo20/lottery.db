# 5. Analytics Audit

**Document type:** Audit report (documentation only)
**Project:** Lottery analysis suite
**Root:** `D:\xampp\htdocs\Lottery`

Scope: the statistical engine modules in `analytics/`, the ensemble predictor in `ensemble_model/`, the trend scanner, and the numeric artifacts they produce.

---

## 5.1 Module Assessment (evidence-based)

| Module | File | Assessment |
|---|---|---|
| Probability engine | `analytics/probability_engine.py` | Sound: digit/pair/triple frequencies, lift, z-scores. Readable and coherent |
| Advanced probability | `analytics/probability_advanced.py` | Sound supplementary statistics |
| Pattern engine | `analytics/pattern_engine.py` | Sound pattern analysis (26,896 bytes) |
| Heatmap engine | `analytics/heatmap_engine.py` | Sound heatmap analysis |
| Monte Carlo engine | `analytics/monte_carlo_engine.py` | Sound simulation; `database/simulation/monte_carlo_results.json` (100,000 sims, 459 draws) |
| Feature engineering | `analytics/feature_engineering.py` | Writes `database/dataset/lottery_features.csv` (stale — see §5.4) |
| Temporal weight engine | `analytics/temporal_weight_engine.py` | Writes `lottery_temporal_features.csv` (stale — see §5.4) |
| Result fetcher | `analytics/result_fetcher.py` | Regex-based extraction; fragmented verification path |
| Performance analyzer | `analytics/performance_analyzer.py` | Analyzes `prediction_history.csv` → `accuracy_report.json` |
| Explainable AI | `analytics/explainable_ai.py` | Produces per-position TH/EN explanations — but recomputes factors with its own `FACTOR_WEIGHTS` (lines 44–49) instead of reading the model's actual contributions (see `06-ai-audit.md` §6.6) |
| Backtest engine | `analytics/backtest_engine.py` | **Non-functional** — see §5.2 |
| Prediction pipeline | `analytics/predict_pipeline.py` | Orchestrator; "pattern" step non-functional — see §5.5 |
| Prediction history | `analytics/prediction_history.py` | Logs predictions + actuals; currently storing fabricated actuals — see §5.3 |
| Strategy optimizer | `analytics/strategy_optimizer.py` | Present; limited integration evidence |

## 5.2 Backtest Engine — Critical Defects

Evidence (`analytics/backtest_engine.py`):
1. **Random predictions.** Lines 79–82: `# TODO: Connect real predictor here, e.g., EnsemblePredictor` followed by `return f"{random.randint(0, 999999):06d}"`. The backtest never uses the model.
2. **Broken accuracy formula.** Line 138: `"accuracy_score": round((total_pos_hits / 6) * 100, 2)` — omits division by `total_draws`. Verified output artifact: `database/backtest/backtest_report.json` contains `accuracy_score: 3766.67` (≈3,767%), which is mathematically impossible for an accuracy percentage.

Result artifact summary (`database/backtest/backtest_report.json`):
- `total_draws: 359`, `exact_matches: 0`, `average_digit_hits: 2.29`, `accuracy_score: 3766.67`.

**Conclusion:** every figure derived from the backtest — including the published "Grade C (40/100)" — is not an evaluation of the AI model. It is a random-number baseline with an invalid formula.

## 5.3 Fabricated Accuracy Records — Critical Defect

Evidence:
- `database/predictions/prediction_history.json`: two entries target `2026-04-01` and record `"actual_result": "123456"`.
- `database/dataset/lottery_history.csv` (row 8): the actual first prize for `2026-04-01` is **`292514`**.
- `database/predictions/prediction_history.csv` mirrors the `123456` value.
- Downstream derived metrics are therefore corrupt:
  - Root `performance.json`: `evaluated: 2`, `avg_digit_hits: 4.0`, `avg_positional_hits: 0.0`, `exact_matches: 0`.
  - `analytics/model_adjustments.json`: 5 entries; last `2026-03-14`; `model_score: 40.0` (source of the "Grade C").

**Conclusion:** the recorded model accuracy is computed against data that does not correspond to reality. The origin of `"123456"` (manual entry vs. bug) cannot be determined from the repository — *not enough evidence*.

## 5.4 Stale Derived Datasets

Evidence (script-verified):
- `database/dataset/lottery_history.csv`: **467 rows**, through `2026-07-01`.
- `database/dataset/lottery_features.csv` and `database/dataset/lottery_temporal_features.csv`: **459 rows each**, latest `2026-03-01`.

Divergence: 8 draws (`2026-03-16` … `2026-07-01`) missing. The scheduler contains a feature/temporal rebuild trigger (`ai_engine/scrapers/update_scheduler.py:382-396`), but the output shows it has not produced rows past `2026-03-01`. Why it stopped is not determinable from source alone — *not enough evidence*.

Consumers of the stale data: `analytics/feature_engineering.py`, `analytics/temporal_weight_engine.py`, and the orphaned `ai_engine/generator/candidate_generator.py`.

## 5.5 Pipeline "Pattern" Step — Non-Functional

Evidence (`analytics/predict_pipeline.py:62`): the "pattern" analysis step is a non-functional set comprehension that simply returns the last 5 draws as candidates. It does not invoke the real `analytics/pattern_engine.py`.

Impact: pipeline candidates are generated primarily by probability signals; the pattern signal is effectively absent.

## 5.6 Orphaned Module

Evidence: `ai_engine/generator/candidate_generator.py` (2,370 bytes) reads `database/dataset/lottery_temporal_features.csv` directly and is **never referenced** by any pipeline or API (repository grep: "No files found" for callers). It is dead code carrying stale-data consumption.

## 5.7 Data-Flow Integrity Summary

| Stage | Status |
|---|---|
| Master history → CSV | OK (467 rows, desc, verified) |
| Feature/temporal CSVs | Stale by 8 draws |
| Backtest report | Invalid (random predictions + broken formula) |
| Prediction history | Contains fabricated actual `123456` |
| Performance metrics | Derived from fabricated actuals |
| Pipeline cache | Present (1,272 lines) with divergent `pipeline_output.json` |
| Pattern signal | Non-functional in pipeline |

## 5.8 Analytics Scores

| Category | Score | Rationale |
|---|---|---|
| Statistical engine soundness | **7 / 10** | Individual modules coherent; overlap in scope |
| Backtest / validation | **1 / 10** | Random predictions; broken formula |
| Data integrity | **2 / 10** | Fabricated actuals; stale features |
| Output consistency | **4 / 10** | Divergent schemas across logs/caches |

## 5.9 Recommendations (documentation only)

1. Re-run the backtest against the real predictor using a walk-forward split; fix the accuracy formula to `(total_pos_hits / (6 * total_draws)) * 100`.
2. Correct or remove the fabricated `123456` records; re-derive `performance.json`, `accuracy_report.json`, and `model_adjustments.json` from real draws.
3. Regenerate feature/temporal CSVs (or fix the scheduler trigger).
4. Implement the pipeline "pattern" step via `pattern_engine.py`, or remove it.
5. Delete the orphaned `candidate_generator.py` or wire it into the pipeline.
6. Unify prediction-log and pipeline-output schemas.

**Cross-references:** `reports/audit/03-architecture-audit.md` §3.4–§3.5, `reports/audit/06-ai-audit.md`, `reports/audit/10-development-roadmap.md`.
