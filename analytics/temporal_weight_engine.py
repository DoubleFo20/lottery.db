import csv
import math
from datetime import datetime

INPUT_PATH = "database/dataset/lottery_features.csv"
OUTPUT_PATH = "database/dataset/lottery_temporal_features.csv"


class TemporalWeightEngine:

    def __init__(self):

        self.rows = []

    def load_dataset(self):

        with open(INPUT_PATH, "r", encoding="utf-8") as f:

            reader = csv.DictReader(f)

            for row in reader:

                row["draw_date"] = datetime.strptime(row["draw_date"], "%Y-%m-%d")

                self.rows.append(row)

    def compute_weights(self):

        newest = max(r["draw_date"] for r in self.rows)

        for r in self.rows:

            age = (newest - r["draw_date"]).days

            weight = math.exp(-0.002 * age)

            r["temporal_weight"] = round(weight, 5)

    def save(self):

        fieldnames = list(self.rows[0].keys())

        with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:

            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()

            for r in self.rows:

                r["draw_date"] = r["draw_date"].strftime("%Y-%m-%d")

                writer.writerow(r)

    def run(self):

        print("Loading feature dataset...")
        self.load_dataset()

        print("Computing temporal weights...")
        self.compute_weights()

        print("Saving temporal dataset...")
        self.save()

        print("Temporal weighting complete")
        print(f"Rows: {len(self.rows)}")
        print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":

    engine = TemporalWeightEngine()
    engine.run()