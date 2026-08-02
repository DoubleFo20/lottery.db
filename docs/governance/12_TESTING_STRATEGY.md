# 12 — Testing Strategy

**Status: Draft**

## Purpose

Defines how the Lottery project is verified: test layers, evaluation methodology, and the definition of done. Currently the project has zero tests (D19); this document sets the target.

## Scope

- Test layers and framework conventions.
- Evaluation methodology (walk-forward, baselines).
- Verification gates for `prompts/test.md` and `prompts/review.md`.

## Responsibilities

- Define the testing standard all new code must meet.
- Guide the addition of test infrastructure (Phase 4, R21).
- Define honest evaluation for AI components.

## Test Pyramid

1. **Unit tests** — individual engines and helpers (probability, pattern, feature, temporal).
2. **Integration tests** — pipeline stage wiring; API contracts against fixtures.
3. **Evaluation tests** — walk-forward model evaluation and baseline comparison.

## Frameworks

- Python: `pytest` (fixtures based on known, tiny datasets).
- PHP: `PHPUnit` for the canonical API layer once consolidated.
- Dashboards: lint + a smoke check of data-contract shapes (see `docs/reference/05_API_SPECIFICATION.md`).

## Evaluation Methodology

- **Walk-forward only.** Never evaluate a model on data used to train or fit it.
- **Real actuals only.** Metrics must derive from `lottery_history.csv`, never from fabricated records (D3).
- **Random baseline.** Every model result is compared against a measured random baseline (R8).
- **Calibration check.** Confidence claims must be validated or labeled as relative (R16).

## Definition of Done

A change is done when:

1. Relevant tests exist and pass.
2. Any affected evaluation is walk-forward and uses real actuals.
3. The change respects `docs/governance/11_CODING_STANDARDS.md`.
4. Human sign-off is recorded.

## Verification Gates

| Stage | Gate |
|---|---|
| Before commit | Compile/lint; targeted unit tests |
| Before merge | Full test suite; evaluation tests if AI affected |
| Periodic | Audit (`prompts/audit.md`) refreshes the snapshot and debt register |

## References

- `docs/governance/11_CODING_STANDARDS.md` — contribution rules
- `docs/reference/05_API_SPECIFICATION.md` — API contract tests
- `docs/reference/06_AI_PIPELINE.md` — AI contracts under test
- `docs/reference/07_ANALYTICS_ENGINE.md` — engine unit/integration tests
- `docs/governance/08_ROADMAP.md` — Phase 4 testing work
- `prompts/test.md` — testing workflow
