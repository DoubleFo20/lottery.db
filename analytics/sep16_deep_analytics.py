"""
analytics/sep16_deep_analytics.py
===================================
Deep Historical & Predictive Analysis for Thai Government Lottery
Focus: September 16 Draw Analysis (งวดประจำวันที่ 16 กันยายน)
Incorporates Recency Weighting, Positional Markov Chains, and Ensemble Probabilities.
"""

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "database" / "dataset" / "lottery_history.csv"
OUT_JSON = BASE_DIR / "database" / "predictions" / "sep16_analytics_prediction.json"


def load_dataset():
    records = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d_str = row["draw_date"].strip()
            if not d_str:
                continue
            dt = datetime.strptime(d_str, "%Y-%m-%d")
            fp = row["first_prize"].strip().zfill(6)
            last2 = row["last2"].strip().zfill(2)
            top2 = fp[-2:]
            top3 = fp[-3:]
            
            f3 = [row.get("front3_1", "").strip(), row.get("front3_2", "").strip()]
            b3 = [row.get("back3_1", "").strip(), row.get("back3_2", "").strip()]
            f3 = [x for x in f3 if x]
            b3 = [x for x in b3 if x]

            digits = [int(fp[i]) for i in range(6)]

            records.append({
                "date": d_str,
                "dt": dt,
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "first_prize": fp,
                "last2": last2,
                "top2": top2,
                "top3": top3,
                "front3": f3,
                "back3": b3,
                "digits": digits
            })
    # Sort chronological: oldest to newest
    records.sort(key=lambda x: x["dt"])
    return records


def calculate_recency_weight(year, target_year=2026):
    """
    Tiered Recency Weighting:
    - 1-5 years ago (2022-2026): Weight = 3.0
    - 6-10 years ago (2017-2021): Weight = 2.0
    - 11-15 years ago (2012-2016): Weight = 1.0
    - 16-20+ years ago (<= 2011): Weight = 0.5
    """
    age = target_year - year
    if age <= 4:
        return 3.0
    elif age <= 9:
        return 2.0
    elif age <= 14:
        return 1.0
    else:
        return 0.5


def run_analysis():
    records = load_dataset()
    total_draws = len(records)
    latest_draw = records[-1]
    target_year = 2026

    # 1. Filter: Specific to Sep 16
    sep16_draws = [r for r in records if r["month"] == 9 and r["day"] == 16]
    # Filter: All September draws
    sep_all_draws = [r for r in records if r["month"] == 9]

    # --- Sep 16 Specific Stats ---
    sep16_top2_counts = Counter()
    sep16_top2_weighted = defaultdict(float)
    sep16_last2_counts = Counter()
    sep16_last2_weighted = defaultdict(float)
    sep16_top3_counts = Counter()
    sep16_digits_pos = [Counter() for _ in range(6)]

    for r in sep16_draws:
        w = calculate_recency_weight(r["year"], target_year)
        sep16_top2_counts[r["top2"]] += 1
        sep16_top2_weighted[r["top2"]] += w

        sep16_last2_counts[r["last2"]] += 1
        sep16_last2_weighted[r["last2"]] += w

        sep16_top3_counts[r["top3"]] += 1
        for pos in range(6):
            sep16_digits_pos[pos][r["digits"][pos]] += 1

    # --- Global 20-Year Stats with Recency Weighting ---
    global_top2_weighted = defaultdict(float)
    global_last2_weighted = defaultdict(float)
    global_top3_weighted = defaultdict(float)
    global_digits_pos_weighted = [defaultdict(float) for _ in range(6)]

    for r in records:
        w = calculate_recency_weight(r["year"], target_year)
        global_top2_weighted[r["top2"]] += w
        global_last2_weighted[r["last2"]] += w
        global_top3_weighted[r["top3"]] += w
        for pos in range(6):
            global_digits_pos_weighted[pos][r["digits"][pos]] += w

    # --- 1st-Order Markov State Transition from Latest Draw ---
    # Latest draw digits
    last_fp = latest_draw["first_prize"]
    last_l2 = latest_draw["last2"]
    
    # Transition probabilities for 2-digit pairs
    # P(top2_next | top2_prev)
    top2_transitions = defaultdict(Counter)
    last2_transitions = defaultdict(Counter)
    pos_transitions = [defaultdict(Counter) for _ in range(6)]

    for i in range(len(records) - 1):
        curr_r = records[i]
        next_r = records[i + 1]
        top2_transitions[curr_r["top2"]][next_r["top2"]] += 1
        last2_transitions[curr_r["last2"]][next_r["last2"]] += 1
        for pos in range(6):
            pos_transitions[pos][curr_r["digits"][pos]][next_r["digits"][pos]] += 1

    # --- Prediction Model Fusion ---
    # Probability computation for 2 ตัวบน (00-99)
    top2_scores = {}
    for num in range(100):
        s_num = f"{num:02d}"
        # Component 1: Sep 16 specific weighted score (weight = 0.40)
        score_sep16 = sep16_top2_weighted[s_num]
        # Component 2: Global recency-weighted score (weight = 0.35)
        score_global = global_top2_weighted[s_num]
        # Component 3: Markov transition from latest draw (weight = 0.25)
        trans_count = top2_transitions[latest_draw["top2"]][s_num]
        
        # Combined score with prior smoothing
        combined = (score_sep16 * 4.0) + (score_global * 0.5) + (trans_count * 2.0)
        top2_scores[s_num] = combined

    # Softmax scaling to get exact probabilities (summing to 100%)
    max_s = max(top2_scores.values()) if top2_scores else 1.0
    exp_top2 = {k: math.exp((v - max_s) / 5.0) for k, v in top2_scores.items()}
    sum_exp_top2 = sum(exp_top2.values())
    top2_probs = {k: (v / sum_exp_top2) * 100.0 for k, v in exp_top2.items()}
    ranked_top2 = sorted(top2_probs.items(), key=lambda x: x[1], reverse=True)

    # Probability computation for 2 ตัวล่าง (00-99)
    last2_scores = {}
    for num in range(100):
        s_num = f"{num:02d}"
        score_sep16 = sep16_last2_weighted[s_num]
        score_global = global_last2_weighted[s_num]
        trans_count = last2_transitions[latest_draw["last2"]][s_num]
        
        combined = (score_sep16 * 4.0) + (score_global * 0.5) + (trans_count * 2.0)
        last2_scores[s_num] = combined

    max_s_l2 = max(last2_scores.values()) if last2_scores else 1.0
    exp_last2 = {k: math.exp((v - max_s_l2) / 5.0) for k, v in last2_scores.items()}
    sum_exp_last2 = sum(exp_last2.values())
    last2_probs = {k: (v / sum_exp_last2) * 100.0 for k, v in exp_last2.items()}
    ranked_last2 = sorted(last2_probs.items(), key=lambda x: x[1], reverse=True)

    # Probability computation for 3 ตัวบน (Top candidates from pos 4,5,6 fusion)
    # Determine top digits per position 4, 5, 6
    pos_top_digits = []
    for pos in [3, 4, 5]: # digits 4, 5, 6
        p_scores = {}
        for d in range(10):
            s_sep = sep16_digits_pos[pos][d] * 3.0
            s_glob = global_digits_pos_weighted[pos][d]
            s_trans = pos_transitions[pos][latest_draw["digits"][pos]][d] * 2.0
            p_scores[d] = s_sep + s_glob + s_trans
        best_digits = sorted(p_scores.items(), key=lambda x: x[1], reverse=True)
        pos_top_digits.append(best_digits)

    # Generate 3-digit combinations
    top3_candidates = {}
    for d4, s4 in pos_top_digits[0][:4]:
        for d5, s5 in pos_top_digits[1][:4]:
            for d6, s6 in pos_top_digits[2][:4]:
                comb = f"{d4}{d5}{d6}"
                # Historical bonus
                h_bonus = sep16_top3_counts[comb] * 5.0 + global_top3_weighted[comb] * 2.0
                score = (s4 * 0.3) + (s5 * 0.35) + (s6 * 0.35) + h_bonus
                top3_candidates[comb] = score

    max_top3 = max(top3_candidates.values()) if top3_candidates else 1.0
    exp_top3 = {k: math.exp((v - max_top3) / 10.0) for k, v in top3_candidates.items()}
    sum_exp_top3 = sum(exp_top3.values())
    top3_probs = {k: (v / sum_exp_top3) * 100.0 for k, v in exp_top3.items()}
    ranked_top3 = sorted(top3_probs.items(), key=lambda x: x[1], reverse=True)

    # Compile Comprehensive Analytics Output
    output_payload = {
        "metadata": {
            "target_draw": "2026-09-16",
            "target_draw_th": "16 กันยายน 2569",
            "latest_historical_draw": latest_draw["date"],
            "latest_first_prize": latest_draw["first_prize"],
            "latest_last2": latest_draw["last2"],
            "total_historical_draws": total_draws,
            "sep16_sample_size_years": len(sep16_draws),
            "generated_at": datetime.now().isoformat()
        },
        "sep16_historical_draws": [
            {
                "date": r["date"],
                "year": r["year"],
                "first_prize": r["first_prize"],
                "top2": r["top2"],
                "last2": r["last2"],
                "top3": r["top3"],
                "weight": calculate_recency_weight(r["year"], target_year)
            }
            for r in sep16_draws
        ],
        "top_predictions": {
            "top2_upper": [
                {
                    "rank": i + 1,
                    "number": num,
                    "probability_pct": round(prob, 2),
                    "sep16_raw_freq": sep16_top2_counts[num],
                    "sep16_weighted_freq": round(sep16_top2_weighted[num], 2),
                    "tier": "HOT" if i < 5 else ("WARM" if i < 15 else "NEUTRAL")
                }
                for i, (num, prob) in enumerate(ranked_top2[:15])
            ],
            "last2_lower": [
                {
                    "rank": i + 1,
                    "number": num,
                    "probability_pct": round(prob, 2),
                    "sep16_raw_freq": sep16_last2_counts[num],
                    "sep16_weighted_freq": round(sep16_last2_weighted[num], 2),
                    "tier": "HOT" if i < 5 else ("WARM" if i < 15 else "NEUTRAL")
                }
                for i, (num, prob) in enumerate(ranked_last2[:15])
            ],
            "top3_combinations": [
                {
                    "rank": i + 1,
                    "number": num,
                    "probability_pct": round(prob, 2),
                    "historical_sep16_hits": sep16_top3_counts[num],
                    "tier": "HOT" if i < 5 else "WARM"
                }
                for i, (num, prob) in enumerate(ranked_top3[:10])
            ]
        },
        "positional_hot_cold": {
            f"digit_{pos+1}": {
                "hot_digits": [d for d, _ in sep16_digits_pos[pos].most_common(3)],
                "frequencies": dict(sep16_digits_pos[pos].most_common(10))
            }
            for pos in range(6)
        }
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    print(f"=== Deep Analytics & Prediction Complete ===")
    print(f"Target: {output_payload['metadata']['target_draw_th']}")
    print(f"Historical Sep 16 Draws: {len(sep16_draws)} draws evaluated across 20 years")
    print("\n--- TOP 5 PREDICTED: 2 ตัวบน (2-Digit Upper) ---")
    for item in output_payload["top_predictions"]["top2_upper"][:5]:
        print(f"#{item['rank']} [{item['number']}]: Prob={item['probability_pct']}% | Sep16 Hits={item['sep16_raw_freq']} (Wt={item['sep16_weighted_freq']}) | Tier={item['tier']}")

    print("\n--- TOP 5 PREDICTED: 2 ตัวล่าง (2-Digit Lower) ---")
    for item in output_payload["top_predictions"]["last2_lower"][:5]:
        print(f"#{item['rank']} [{item['number']}]: Prob={item['probability_pct']}% | Sep16 Hits={item['sep16_raw_freq']} (Wt={item['sep16_weighted_freq']}) | Tier={item['tier']}")

    print("\n--- TOP 5 PREDICTED: 3 ตัวบน (3-Digit Combinations) ---")
    for item in output_payload["top_predictions"]["top3_combinations"][:5]:
        print(f"#{item['rank']} [{item['number']}]: Prob={item['probability_pct']}% | Tier={item['tier']}")

    return output_payload


if __name__ == "__main__":
    run_analysis()
