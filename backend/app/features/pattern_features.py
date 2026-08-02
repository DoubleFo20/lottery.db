class PatternFeatures:
    @staticmethod
    def has_repeated_digits(num: str) -> int:
        """Returns 1 if any digit is repeated consecutively, 0 otherwise."""
        if not num or len(num) < 2: return 0
        for i in range(len(num) - 1):
            if num[i] == num[i+1]:
                return 1
        return 0

    @staticmethod
    def has_consecutive_digits(num: str) -> int:
        """Returns 1 if there are any sequential digits (e.g. '12' or '54'), 0 otherwise."""
        if not num or len(num) < 2: return 0
        for i in range(len(num) - 1):
            diff = abs(int(num[i]) - int(num[i+1]))
            if diff == 1:
                return 1
        return 0

    @staticmethod
    def get_odd_even_ratio(num: str) -> float:
        """Returns the ratio of odd digits to total digits."""
        if not num: return 0.0
        odds = sum(1 for d in num if d.isdigit() and int(d) % 2 != 0)
        return odds / len(num)

    @staticmethod
    def get_high_low_ratio(num: str) -> float:
        """Returns the ratio of high digits (5-9) to total digits."""
        if not num: return 0.0
        highs = sum(1 for d in num if d.isdigit() and int(d) >= 5)
        return highs / len(num)
