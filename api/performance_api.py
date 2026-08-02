import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
HISTORY_JSON = BASE_DIR / "database" / "predictions" / "prediction_history.json"


def load_history():
    if not HISTORY_JSON.exists():
        return []

    return json.loads(HISTORY_JSON.read_text(encoding="utf-8"))


def get_performance_metrics():
    data = load_history()

    evaluated = [e for e in data if e.get("accuracy")]

    if not evaluated:
        return {
            "total_predictions": len(data),
            "exact_matches": 0,
            "avg_pos_hits": 0,
            "avg_digit_hits": 0
        }

    exact = sum(1 for e in evaluated if e["accuracy"]["any_exact_match"])

    pos_hits = [e["accuracy"]["avg_positional_hits"] for e in evaluated]
    dig_hits = [e["accuracy"]["avg_digit_hits"] for e in evaluated]

    return {
        "total_predictions": len(data),
        "exact_matches": exact,
        "avg_pos_hits": round(sum(pos_hits) / len(pos_hits), 2),
        "avg_digit_hits": round(sum(dig_hits) / len(dig_hits), 2)
    }


if __name__ == "__main__":
    print(json.dumps(get_performance_metrics(), indent=2))