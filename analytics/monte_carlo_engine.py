"""
Lottery AI Monte Carlo Simulation Engine
========================================
Simulates many lottery draws using statistical distributions
learned from historical data to estimate most likely patterns.
"""

import argparse
import csv
import json
import random
from collections import Counter
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
SIM_DIR  = BASE_DIR / "database" / "simulation"
RES_JSON = SIM_DIR / "monte_carlo_results.json"
RES_CSV  = SIM_DIR / "monte_carlo_top100.csv"


def load_history() -> list[str]:
    """Load historical lottery numbers."""
    history = []
    if not CSV_PATH.exists():
        print(f"[ERROR] Dataset not found: {CSV_PATH}")
        return history

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_val = row.get("draw_date", "")
            # Reconstruct the 6-digit winning number
            digits = []
            valid = True
            for i in range(1, 7):
                d = row.get(f"digit{i}", "").strip()
                if not d:
                    valid = False
                    break
                digits.append(d)
            
            if valid and date_val:
                history.append("".join(digits))
                
    return history


def learn_digit_distribution(history: list[str]) -> dict:
    """Calculate frequency for each position."""
    if not history:
        return {}
        
    # Initialize counts
    counts = {f"pos{i+1}": Counter() for i in range(6)}
    
    for number in history:
        if len(number) == 6:
            for i in range(6):
                counts[f"pos{i+1}"][number[i]] += 1
                
    total_draws = len(history)
    distribution = {}
    
    for pos, counter in counts.items():
        pos_dist = {}
        for digit in "0123456789":
            # Probability calculation
            pos_dist[digit] = counter.get(digit, 0) / total_draws
        distribution[pos] = pos_dist
        
    return distribution


def simulate_draw(distribution: dict) -> str:
    """Generate a synthetic 6-digit number based on learned distributions."""
    digits = []
    
    for i in range(1, 7):
        pos_key = f"pos{i}"
        pos_dist = distribution.get(pos_key, {})
        
        # Prepare data for random.choices
        population = list(pos_dist.keys())
        weights = list(pos_dist.values())
        
        # Select one digit based on weights
        chosen_digit = random.choices(population, weights=weights, k=1)[0]
        digits.append(chosen_digit)
        
    return "".join(digits)


def run_simulation(num_simulations: int = 100000) -> dict:
    """Simulate many draws using learned distributions."""
    history = load_history()
    if not history:
        print("[WARN] Empty history. Cannot run simulation.")
        return {}

    print(f"[INFO] Learning distributions from {len(history)} historical draws...")
    distribution = learn_digit_distribution(history)
    
    print(f"[INFO] Running {num_simulations:,} Monte Carlo simulations...")
    results_counter = Counter()
    
    for _ in range(num_simulations):
        synthetic_number = simulate_draw(distribution)
        results_counter[synthetic_number] += 1
        
    # Extract top candidates
    top_candidates = results_counter.most_common(100)
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "simulations_run": num_simulations,
        "historical_draws_used": len(history),
        "distribution": distribution,
        "top_candidates": [
            {"number": num, "frequency": count, "probability": count / num_simulations}
            for num, count in top_candidates
        ]
    }
    
    return summary


def save_results(summary: dict):
    """Save simulation results to JSON and top 100 to CSV."""
    if not summary:
        print("[WARN] No results to save.")
        return
        
    SIM_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with open(RES_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    # Save CSV (Top 100)
    top_candidates = summary.get("top_candidates", [])
    with open(RES_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "number", "frequency", "probability_pct"])
        
        for i, cand in enumerate(top_candidates, 1):
            writer.writerow([
                i,
                cand["number"],
                cand["frequency"],
                f"{cand['probability'] * 100:.4f}%"
            ])
            
    print(f"[INFO] Results saved to:\n  - {RES_JSON}\n  - {RES_CSV}")


def main():
    parser = argparse.ArgumentParser(description="Lottery Monte Carlo Simulation Engine")
    parser.add_argument("--run", action="store_true", help="Run the Monte Carlo simulation")
    parser.add_argument("--sims", type=int, default=100000, help="Number of simulations to run")
    args = parser.parse_args()

    if args.run:
        summary = run_simulation(args.sims)
        if summary:
            save_results(summary)
            
            top_cans = summary.get("top_candidates", [])
            print("\n===============================")
            print(" Monte Carlo Simulation Report")
            print("===============================")
            print(f" Simulations run: {summary['simulations_run']:,}")
            print("\n Top predicted numbers:")
            for i, cand in enumerate(top_cans[:10]):
                print(f" {i+1:2d}. {cand['number']} (freq: {cand['frequency']})")
            print("===============================\n")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
