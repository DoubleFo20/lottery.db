import csv
import math
from collections import Counter

INPUT_PATH = "database/dataset/lottery_history.csv"
OUTPUT_PATH = "database/dataset/lottery_features.csv"


class FeatureEngineering:

    def __init__(self):
        self.rows = []

    def load_dataset(self):

        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:

                digits = [
                    int(row["digit1"]),
                    int(row["digit2"]),
                    int(row["digit3"]),
                    int(row["digit4"]),
                    int(row["digit5"]),
                    int(row["digit6"]),
                ]

                self.rows.append({
                    "draw_date": row["draw_date"],
                    "digits": digits
                })

    def digit_sum(self, digits):
        return sum(digits)

    def odd_even(self, digits):

        odd = sum(d % 2 for d in digits)
        even = 6 - odd

        return odd, even

    def repeat_count(self, digits):

        counts = Counter(digits)

        return sum(1 for c in counts.values() if c > 1)

    def entropy(self, digits):

        counts = Counter(digits)

        total = len(digits)

        ent = 0

        for c in counts.values():
            p = c / total
            ent -= p * math.log2(p)

        return ent

    def mirror_score(self, digits):

        score = 0

        if digits[0] == digits[5]:
            score += 1
        if digits[1] == digits[4]:
            score += 1
        if digits[2] == digits[3]:
            score += 1

        return score

    def transition_score(self, digits):

        score = 0

        for i in range(5):
            diff = abs(digits[i] - digits[i+1])

            if diff <= 3:
                score += 1

        return score

    def build_features(self):

        features = []

        for r in self.rows:

            digits = r["digits"]

            digit_sum = self.digit_sum(digits)
            odd, even = self.odd_even(digits)
            repeat = self.repeat_count(digits)
            ent = self.entropy(digits)
            mirror = self.mirror_score(digits)
            transition = self.transition_score(digits)

            features.append({

                "draw_date": r["draw_date"],

                "digit1": digits[0],
                "digit2": digits[1],
                "digit3": digits[2],
                "digit4": digits[3],
                "digit5": digits[4],
                "digit6": digits[5],

                "digit_sum": digit_sum,
                "odd_count": odd,
                "even_count": even,
                "repeat_count": repeat,
                "entropy": round(ent,4),
                "mirror_score": mirror,
                "transition_score": transition

            })

        return features

    def save(self, rows):

        fieldnames = rows[0].keys()

        with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:

            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()

            for r in rows:
                writer.writerow(r)

    def run(self):

        print("Loading dataset...")
        self.load_dataset()

        print("Generating features...")
        features = self.build_features()

        print("Saving feature dataset...")
        self.save(features)

        print("Feature dataset created")
        print(f"Rows: {len(features)}")
        print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":

    engine = FeatureEngineering()
    engine.run()