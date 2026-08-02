# 6. AI Audit

**Document type:** Audit report (documentation only)
**Project:** Lottery analysis suite
**Root:** `D:\xampp\htdocs\Lottery`

Scope: the AI/ML components — ensemble prediction, self-learning, explainable AI, and the ML readiness of the stack.

---

## 6.1 Components Inventory

| Component | Files | Role |
|---|---|---|
| Ensemble predictor | `ensemble_model/predictor.py` | Fuses 8 statistical signals → per-position scores → beam-search candidates |
| Self-learning | `ai_engine/self_learning.py`, `ai_engine/self_learning_manager.py` | Evaluate, adapt weights, persist to `ensemble_weights.json` |
| Explainable AI | `analytics/explainable_ai.py` | Per-position Thai/English explanations |
| Trend scanner | `trend_scanner/trend_scanner.py` | Streak/spike/surge detection (reporting only) |
| Candidate generation | `ai_engine/generator/candidate_generator.py` | Orphaned (see §6.7) |

## 6.2 Self-Learning Is Disconnected — Critical

Evidence:
- `ai_engine/self_learning.py` and `ai_engine/self_learning_manager.py` evaluate predictions and persist adapted weights to `database/predictions/ensemble_weights.json`.
- `ensemble_model/predictor.py:51` defines `WEIGHTS = {...}` as a **hardcoded constant**.
- Grep for the weight-file path confirms it is only referenced by the self-learning modules, `api/run_pipeline.py:67` (echoes `pred_data`), and `analytics/explainable_ai.py` — **never loaded into the predictor**.
- Observed weights file (`database/predictions/ensemble_weights.json`): positional_freq 0.2, rolling_heat 0.2, conditional 0.15, transition 0.1, pair_lift 0.1, pattern_hot 0.1, gap_overdue 0.08, temporal_trend 0.07.

**Conclusion:** the adapt→persist→consume chain is broken at the final link. Every "adaptation" has zero effect on actual predictions. The system's flagship self-learning feature is non-functional end-to-end.

## 6.3 Dual Prediction Logs — No Single Source of Truth

Evidence:
- `database/predictions/prediction_history.json` — written by `analytics/prediction_history.py`.
- `database/predictions/prediction_log.json` — written by `ai_engine/self_learning.py`.
- The two logs have divergent content and no linkage. Any evaluation based on one log will disagree with the other.

## 6.4 Transition Matrix Direction — Critical Signal Bug

Evidence (`ensemble_model/predictor.py`):
- The module reads the dataset which is verified **descending-ordered** (newest-first); a code comment at line 95 notes `rows are desc-sorted`.
- `_transition_matrix` (lines 123–138) iterates `for idx in range(len(rows) - 1): cur = rows[idx]; nxt = rows[idx + 1]` — with descending rows, `rows[idx + 1]` is chronologically **earlier**.
- The documented intent is `P(digit_next_draw | digit_this_draw)`, but the code encodes `P(previous_draw | current_draw)` — i.e., the direction is reversed.
- Scoring (lines 311–313) then queries the matrix with the latest draw's digit, compounding the error.

**Conclusion:** a core signal is directionally incorrect; the transition contribution actively encodes the wrong conditional.

## 6.5 Confidence Is Not Calibrated

Evidence:
- Observed artifacts (e.g., `database/predictions/pipeline_cache.json`) show the top candidate consistently at `confidence: 100.0`, with other candidates near 93–99%.
- The code normalizes confidence relative to the top candidate rather than calibrating against observed draw-outcome probabilities.
- True joint scores in the cache are on the order of `1e-6`.

**Impact:** users are told a candidate is "100% confident" when it is merely the best of a very low-probability set.

## 6.6 Explainable AI Recomputes Rather Than Attributes

Evidence (`analytics/explainable_ai.py:44-49`):
- XAI applies its own `FACTOR_WEIGHTS` grouping and re-derives factor percentages from the pipeline cache rather than reading the predictor's actual per-signal contributions.
- The resulting "probability/heatmap/pattern" percentages are approximations and can diverge from the model's true behavior.

## 6.7 Orphaned / Non-Integrated Components

- `ai_engine/generator/candidate_generator.py`: never invoked by any pipeline (grep: no callers).
- `trend_scanner/trend_scanner.py`: computes streak/spike/surge signals that appear in `pipeline_cache.json` under `analytics` but are **not consumed as weighted ensemble signals** by the predictor.

## 6.8 ML Readiness Assessment

Evidence:
- Runtime has `numpy 2.4.3`, `pandas 3.0.1`, `scikit-learn 1.8.0`, `scipy 1.17.1` installed.
- Repository-wide grep for `numpy|pandas|sklearn|scipy|tensorflow|torch` imports: **No files found**.

**Conclusion:** despite ML libraries being installed, the system uses no machine-learning model. All "AI" behavior is hand-crafted statistical feature fusion. That is not inherently wrong, but:
- There is no train/test split or walk-forward validation anywhere; every computation uses 100% of the data (leakage risk in any future ML work).
- There is no honest baseline comparison; `self_learning_manager.py:214-221` uses a hardcoded "Random Baseline" constant, not a measured value.
- No probability calibration exists.

## 6.9 AI Assessment Scores

| Index | Score | Rationale |
|---|---|---|
| AI readiness | **40 / 100** | Sound statistical foundations; no ML, no validation, no calibration |
| Signal correctness | **3 / 10** | Reversed transition matrix; non-functional pattern step |
| Self-learning | **1 / 10** | Adaptations never consumed by the predictor |
| Explainability | **5 / 10** | Design sound; attribution recomputed, not model-derived |
| Validation | **1 / 10** | No splits, fabricated actuals, random backtest |

## 6.10 Recommendations (documentation only)

1. Make the predictor load `ensemble_weights.json` (with validation/fallback) to close the self-learning loop.
2. Reverse the transition matrix to chronological order (sort rows ascending before building it).
3. Add walk-forward evaluation and a measured random-baseline comparison.
4. Calibrate confidence (e.g., inverse-transformed histogram calibration over walk-forward folds) or label it as relative rank.
5. Make XAI read actual per-signal contributions from the predictor.
6. Unify the two prediction logs.
7. Either wire trend-scanner signals and `candidate_generator.py` into the ensemble or remove them.

**Cross-references:** `reports/audit/05-analytics-audit.md` §5.2–§5.6, `reports/audit/10-development-roadmap.md`.
