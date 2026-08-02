class DigitFeatures:
    @staticmethod
    def get_first_digit(num: str) -> int:
        if not num: return -1
        return int(num[0])

    @staticmethod
    def get_last_digit(num: str) -> int:
        if not num: return -1
        return int(num[-1])

    @staticmethod
    def get_middle_digits(num: str) -> str:
        if not num or len(num) <= 2: return ""
        return num[1:-1]

    @staticmethod
    def get_parity(num: str) -> int:
        """Returns 1 if the number ends in an odd digit, 0 if even."""
        if not num: return -1
        return 1 if int(num[-1]) % 2 != 0 else 0

    @staticmethod
    def get_digit_sum(num: str) -> int:
        if not num: return 0
        return sum(int(d) for d in num if d.isdigit())

    @staticmethod
    def get_unique_digit_count(num: str) -> int:
        if not num: return 0
        return len(set(d for d in num if d.isdigit()))
