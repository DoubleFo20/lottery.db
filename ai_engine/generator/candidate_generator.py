import csv
import random
from collections import Counter

DATASET = "database/dataset/lottery_temporal_features.csv"


class CandidateGenerator:

    def __init__(self):

        self.data = []
        self.digit_prob = [{} for _ in range(6)]

    def load_dataset(self):

        with open(DATASET, "r", encoding="utf-8") as f:

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

                weight = float(row["temporal_weight"])

                self.data.append((digits, weight))

    def build_probability(self):

        pos_counts = [Counter() for _ in range(6)]

        for digits, weight in self.data:

            for i, d in enumerate(digits):

                pos_counts[i][d] += weight

        for i in range(6):

            total = sum(pos_counts[i].values())

            for d in range(10):

                self.digit_prob[i][d] = pos_counts[i][d] / total

    def weighted_choice(self, dist):

        r = random.random()

        s = 0

        for k, v in dist.items():

            s += v

            if r <= s:
                return k

        return random.choice(list(dist.keys()))

    def generate_number(self):

        digits = []

        for i in range(6):

            digits.append(self.weighted_choice(self.digit_prob[i]))

        return digits

    def generate_candidates(self, n=50):

        candidates = []

        for _ in range(n):

            num = self.generate_number()

            candidates.append(num)

        return candidates

    def run(self):

        print("Loading temporal dataset...")
        self.load_dataset()

        print("Building probability model...")
        self.build_probability()

        print("Generating candidate numbers...")

        candidates = self.generate_candidates()

        print("\nTop candidate numbers:\n")

        for c in candidates:

            print("".join(map(str,c)))


if __name__ == "__main__":

    gen = CandidateGenerator()
    gen.run()