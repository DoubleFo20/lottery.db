---
name: dry-spell-remediation
description: Enforces structured remediation when lottery prediction models experience consecutive draw misses (>= 6 draws).
trigger: always_on
---

# Rule: Dry Spell Remediation & Agent Escalation Policy

**Status: Active**

## Purpose
Enforces a standardized investigation, recalibration, and strategy escalation protocol whenever the Lottery AI models experience a consecutive miss streak of 6 or more draws without hitting target prizes (Jackpot 6-digit or Top 2-digit / Banker running combinations).

## Trigger Conditions
1. The Manager Control Center or backtest evaluation reports 6 or more consecutive draws without hitting target prizes.
2. The user executes `/learn` or provides an automated "Dry Spell Advisory Prompt" from the Manager Dashboard.

## Mandatory 5-Step Agent Remediation Protocol
When activated, the AI Agent MUST follow this sequential execution playbook:

### 1. Root Cause & Drift Analysis (RCA)
- Analyze the last 6 draws against active model signals (`rolling_heat`, `transition`, `positional_freq`, `pair_lift`, `temporal_trend`).
- Determine whether data drift occurred (e.g., cold digit surges or rare sequence anomalies).
- Document findings with `file:line` citations and statistical variance metrics.

### 2. Dynamic Weight Recalibration
- Run walk-forward backtesting on the 24 most recent draws.
- Adjust `database/predictions/ensemble_weights.json`:
  - Increase weight for high-recency signals (`rolling_heat` and `temporal_trend`).
  - Decrease weight for long-term unconditioned historical base rates (`positional_freq`).

### 3. Search Space & Diversity Expansion
- Adjust beam search width (`beam_width` from 3 to 4 or 5) in `ensemble_model/predictor.py` to capture broader candidate clusters.
- Apply strict anti-pattern filters (Sum constraint 18-38, Parity balance 2-4 evens, exclude 4-consecutive identical or sequential digits).

### 4. Hedging Portfolio Reallocation (Capital Protection)
- Shift recommended staking allocation toward foundational layers:
  - Boost Banker Digits (เลขวิ่ง / รูด 19 ประตู) allocation to 70% to ensure cash flow continuity and drawdown protection.
  - Maintain 2-Digit Direct/Reverse pairs at 20%.
  - Allocate remaining 10% to 3-Digit Box permutations and 1 Moonshot lottery ticket.

### 5. Retraining, Verification & Deployment
- Re-run pipeline: `python api/run_pipeline.py`.
- Rebuild 3D assets: `npm run build`.
- Run full automated test suite: `python -m pytest tests/` (all tests must pass).
- Synchronize all dashboard mirrors (`index.html`, `strategy.html`, `manager.html`, `3d.html`).
- Commit and push verified changes.
