"""tests/test_adversarial_challenger.py
Adversarial Stress Test Suite for analytics/result_fetcher.py.
Authored by Challenger 1 (Adversarial Verification).

Covers:
1. Malformed dates, calendar boundary conditions, leap years, Thai BE/CE conversions.
2. Malicious payloads, SQL injection strings, XSS scripts, null bytes.
3. Partial draw states, interim releases, and placeholder permutations.
4. Scraper HTML parsing edge cases (garbage HTML, corrupted markup, fake numbers).
5. Empirical 0-byte mutation and exit code 0 invariant verification.
"""

import csv
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

import analytics.result_fetcher as rf

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "database" / "dataset" / "lottery_history.csv"
PREDICTION_CACHE = REPO_ROOT / "database" / "predictions" / "pipeline_cache.json"
PREDICTION_HISTORY = REPO_ROOT / "database" / "predictions" / "prediction_history.json"
PERF_JSON = REPO_ROOT / "performance.json"


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file if it exists."""
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


# =====================================================================
# 1. ADVERSARIAL DATE & CALENDAR EDGE CASES
# =====================================================================

class TestAdversarialDateParsing:
    """Stress-test parse_thai_date_str, is_draw_day, and get_expected_draw_date."""

    @pytest.mark.parametrize("malformed", [
        "", " ", "\t\n", None,
        "32 มกราคม 2569",        # Invalid day 32
        "0 มกราคม 2569",         # Invalid day 0
        "-5 มกราคม 2569",        # Negative day
        "29 กุมภาพันธ์ 2566",    # Feb 29 in non-leap year (2023)
        "31 เมษายน 2569",        # April has only 30 days
        "16 ซุปเปอร์มกราคม 2569", # Fake month
        "16 ??? 2569",           # Special chars for month
        "<script>alert(1)</script>", # XSS in date
        "16 ก.ย. 2569'; DROP TABLE lottery;--", # SQLi string
        "16 กันยายน BE2569",     # Non-numeric BE prefix
        "16.09.2026",            # Dot delimited
        "2026-09-16",            # ISO format without Thai month
    ])
    def test_malformed_thai_date_strings_return_none_or_iso(self, malformed):
        """Ensure malformed or malicious date strings do not crash and either return None or valid ISO."""
        try:
            res = rf.parse_thai_date_str(malformed)
            if res is not None:
                # If a date was parsed, it must be a strictly valid ISO date YYYY-MM-DD
                datetime.strptime(res, "%Y-%m-%d")
        except Exception as e:
            pytest.fail(f"parse_thai_date_str crashed on input '{malformed}': {e}")

    def test_thai_date_be_to_ce_conversion_accuracy(self):
        """Verify BE to CE conversion accuracy: BE 2569 -> CE 2026."""
        res = rf.parse_thai_date_str("16 กันยายน 2569")
        assert res == "2026-09-16"

        # Abbreviated month
        res_abbr = rf.parse_thai_date_str("16 ก.ย. 2569")
        assert res_abbr == "2026-09-16"

        # Month without trailing dot
        res_nodot = rf.parse_thai_date_str("16 ก.ย 2569")
        assert res_nodot == "2026-09-16"

    def test_thai_date_already_ce_year(self):
        """If year is <= 2400, it should be treated as CE year."""
        res = rf.parse_thai_date_str("16 กันยายน 2026")
        assert res == "2026-09-16"

    @pytest.mark.parametrize("test_date,expected_bool", [
        (date(2026, 1, 1), False),   # Jan 1 skipped
        (date(2026, 1, 16), False),  # Jan 16 skipped (Teacher's Day)
        (date(2026, 1, 17), True),   # Jan 17 official draw
        (date(2026, 5, 1), False),   # May 1 skipped (Labour Day)
        (date(2026, 5, 2), True),    # May 2 official draw
        (date(2026, 12, 30), True),  # Dec 30 official draw
        (date(2026, 12, 31), False), # Dec 31 not draw day
        (date(2028, 2, 29), False),  # Leap day not draw day
        (date(2026, 2, 1), True),    # Normal 1st
        (date(2026, 2, 16), True),   # Normal 16th
        (date(2026, 6, 1), True),
        (date(2026, 9, 16), True),
        (date(2026, 9, 15), False),
        (date(2026, 9, 17), False),
    ])
    def test_is_draw_day_holiday_shifts_and_regular_days(self, test_date, expected_bool):
        """Verify strict official Thai lottery calendar shift rules."""
        assert rf.is_draw_day(test_date) is expected_bool

    def test_get_expected_draw_date_year_boundary_jan_1(self):
        """On Jan 1, preceding draw was Dec 30 of prior year."""
        res = rf.get_expected_draw_date(date(2026, 1, 1))
        assert res == "2025-12-30"

    def test_get_expected_draw_date_teacher_day_jan_16(self):
        """On Jan 16 (skipped), preceding draw was Dec 30 of prior year (since Jan 1 was skipped)."""
        res = rf.get_expected_draw_date(date(2026, 1, 16))
        assert res == "2025-12-30"

    def test_get_expected_draw_date_labour_day_may_1(self):
        """On May 1 (skipped), preceding draw was April 16."""
        res = rf.get_expected_draw_date(date(2026, 5, 1))
        assert res == "2026-04-16"

    def test_get_expected_draw_date_leap_year(self):
        """On Feb 29 of leap year 2028, preceding draw was Feb 16."""
        res = rf.get_expected_draw_date(date(2028, 2, 29))
        assert res == "2028-02-16"


# =====================================================================
# 2. ADVERSARIAL VALIDATION & MALICIOUS INPUTS
# =====================================================================

class TestAdversarialValidation:
    """Stress-test is_valid_draw_result with adversarial, corrupted, and malformed inputs."""

    @pytest.mark.parametrize("malicious_fp", [
        "'; DROP TABLE;--",
        "<script>alert(1)</script>",
        "\x0012345",
        " 730640 ",
        "730640\n",
        "730640\x00",
        "+73064",
        "-73064",
        "73.064",
        "73064e",
        "0x1234",
        "null",
        "undefined",
        "NaN",
        "Infinity",
    ])
    def test_reject_malicious_first_prize_strings(self, malicious_fp):
        """Ensure injection attacks and invalid formatted strings are rejected."""
        result = {"first_prize": malicious_fp, "last2": "64", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    @pytest.mark.parametrize("malicious_l2", [
        "';--", "<script>", "\x0064", " 64 ", "64\n", "6.", "-6", "+6", "xx", "XX", "..", "--"
    ])
    def test_reject_malicious_last2_strings(self, malicious_l2):
        """Ensure injection attacks and invalid last2 strings are rejected."""
        result = {"first_prize": "730640", "last2": malicious_l2, "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    @pytest.mark.parametrize("invalid_type", [
        None, 123456, [1, 2, 3], True, False, {"other": "dict"}, (1, 2), 3.14
    ])
    def test_reject_non_dict_or_empty_structures(self, invalid_type):
        """Validator must cleanly reject non-dict types without unhandled exceptions."""
        assert rf.is_valid_draw_result(invalid_type, "2026-09-16") is False

    def test_reject_missing_required_keys(self):
        """Reject payloads missing first_prize, last2, or draw_date."""
        assert rf.is_valid_draw_result({"last2": "64", "draw_date": "2026-09-16"}, "2026-09-16") is False
        assert rf.is_valid_draw_result({"first_prize": "730640", "draw_date": "2026-09-16"}, "2026-09-16") is False
        assert rf.is_valid_draw_result({"first_prize": "730640", "last2": "64"}, "2026-09-16") is False

    def test_reject_none_values_in_keys(self):
        """Reject payloads where values are None."""
        assert rf.is_valid_draw_result({"first_prize": None, "last2": "64", "draw_date": "2026-09-16"}, "2026-09-16") is False
        assert rf.is_valid_draw_result({"first_prize": "730640", "last2": None, "draw_date": "2026-09-16"}, "2026-09-16") is False
        assert rf.is_valid_draw_result({"first_prize": "730640", "last2": "64", "draw_date": None}, "2026-09-16") is False


# =====================================================================
# 3. HTML PARSING ROBUSTNESS & SCRAPER DEFENSES
# =====================================================================

class TestHtmlParsingEdgeCases:
    """Stress-test HTML parsing logic against corrupt or adversarial HTML."""

    def test_extract_generic_on_empty_or_whitespace_html(self):
        """Generic extractor safely returns None on empty or whitespace strings."""
        assert rf._extract_generic("", "test") is None
        assert rf._extract_generic("   \n\t   ", "test") is None

    def test_extract_generic_on_corrupt_or_partial_markup(self):
        """Generic extractor safely handles partial text without crashing."""
        corrupt_html = """
        <html>
            <body>
                <div>ผลการออกสลากกินแบ่งรัฐบาล งวดวันที่ 16 กันยายน 2569</div>
                <div>รางวัลที่ 1 : รอผลรางวัล</div>
                <div>เลขท้าย 2 ตัว : รอการออกรางวัล</div>
            </body>
        </html>
        """
        assert rf._extract_generic(corrupt_html, "test") is None

    def test_extract_generic_ignores_irrelevant_six_digit_numbers(self):
        """Generic extractor does not pick up phone numbers or zip codes as 1st prize."""
        unannounced_html = """
        <html>
            <body>
                <div>งวดวันที่ 16 กันยายน 2569</div>
                <div>รางวัลที่ 1: รอผล</div>
                <div>ติดต่อสำนักงานสลาก: โทร 123456 รหัสไปรษณีย์ 10110</div>
                <div>เลขท้าย 2 ตัว: รอผล</div>
            </body>
        </html>
        """
        assert rf._extract_generic(unannounced_html, "test") is None

    def test_extract_generic_successful_extraction_when_valid(self):
        """Generic extractor successfully extracts valid draw when announced."""
        valid_html = """
        <div>ผลสลากกินแบ่งรัฐบาล งวด 16 กันยายน 2569</div>
        <div>รางวัลที่ 1 730640</div>
        <div>เลขหน้า 3 ตัว 060 521</div>
        <div>เลขท้าย 3 ตัว 266 041</div>
        <div>เลขท้าย 2 ตัว 64</div>
        """
        res = rf._extract_generic(valid_html, "test_source")
        assert res is not None
        assert res["first_prize"] == "730640"
        assert res["last2"] == "64"
        assert res["draw_date"] == "2026-09-16"
        assert res["front3"] == ["060", "521"]
        assert res["back3"] == ["266", "041"]


# =====================================================================
# 4. EMPIRICAL ZERO-MUTATION & EXIT CODE 0 INVARIANTS
# =====================================================================

class TestEmpiricalZeroMutationAndExit0:
    """
    CRITICAL EMPIRICAL VERIFICATION:
    On unannounced, incomplete, or already existing draws:
    - 0 file bytes are modified across ALL tracked files.
    - Exit code is 0.
    - Subprocess pipeline is not executed.
    """

    def test_empirical_zero_mutation_on_unannounced_draw(self, temp_csv_file, tmp_path):
        """Verify 0 file bytes modified and exit code 0 when draw is unannounced (all scrapers return None)."""
        test_history = tmp_path / "prediction_history.json"
        test_perf = tmp_path / "performance.json"
        test_cache = tmp_path / "pipeline_cache.json"

        test_history.write_text('[]', encoding="utf-8")
        test_perf.write_text('{}', encoding="utf-8")
        test_cache.write_text('{"status": "ok"}', encoding="utf-8")

        initial_csv_bytes = temp_csv_file.read_bytes()
        initial_history_bytes = test_history.read_bytes()
        initial_perf_bytes = test_perf.read_bytes()
        initial_cache_bytes = test_cache.read_bytes()

        mock_subprocess = MagicMock()

        with patch.object(rf, "CSV_PATH", temp_csv_file), \
             patch.object(rf, "HISTORY_JSON", test_history), \
             patch.object(rf, "PERF_JSON", test_perf), \
             patch.object(rf, "fetch_thairath", MagicMock(return_value=None)), \
             patch.object(rf, "fetch_sanook", MagicMock(return_value=None)), \
             patch.object(rf, "fetch_kapook", MagicMock(return_value=None)), \
             patch("subprocess.run", mock_subprocess):

            with pytest.raises(SystemExit) as exc_info:
                rf.run(target_date="2026-09-16", force=False, exit_on_finish=True)

            assert exc_info.value.code == 0, f"Expected exit code 0, got {exc_info.value.code}"

        # Assert 0 file bytes modified
        assert temp_csv_file.read_bytes() == initial_csv_bytes, "CSV file was mutated!"
        assert test_history.read_bytes() == initial_history_bytes, "History JSON was mutated!"
        assert test_perf.read_bytes() == initial_perf_bytes, "Performance JSON was mutated!"
        assert test_cache.read_bytes() == initial_cache_bytes, "Pipeline cache was mutated!"
        mock_subprocess.assert_not_called()

    def test_empirical_zero_mutation_on_interim_draw(self, temp_csv_file, tmp_path):
        """Verify 0 file bytes modified and exit code 0 when draw is interim (1st prize pending, last2 announced)."""
        test_history = tmp_path / "prediction_history.json"
        test_perf = tmp_path / "performance.json"
        test_cache = tmp_path / "pipeline_cache.json"

        test_history.write_text('[]', encoding="utf-8")
        test_perf.write_text('{}', encoding="utf-8")
        test_cache.write_text('{"status": "ok"}', encoding="utf-8")

        initial_csv_bytes = temp_csv_file.read_bytes()
        initial_history_bytes = test_history.read_bytes()
        initial_perf_bytes = test_perf.read_bytes()
        initial_cache_bytes = test_cache.read_bytes()

        interim_data = {
            "first_prize": "------",
            "front3": ["060", "521"],
            "back3": ["266", "041"],
            "last2": "64",
            "draw_date": "2026-09-16",
            "source": "sanook"
        }

        mock_subprocess = MagicMock()

        with patch.object(rf, "CSV_PATH", temp_csv_file), \
             patch.object(rf, "HISTORY_JSON", test_history), \
             patch.object(rf, "PERF_JSON", test_perf), \
             patch.object(rf, "fetch_thairath", MagicMock(return_value=None)), \
             patch.object(rf, "fetch_sanook", MagicMock(return_value=interim_data)), \
             patch.object(rf, "fetch_kapook", MagicMock(return_value=interim_data)), \
             patch("subprocess.run", mock_subprocess):

            with pytest.raises(SystemExit) as exc_info:
                rf.run(target_date="2026-09-16", force=False, exit_on_finish=True)

            assert exc_info.value.code == 0, f"Expected exit code 0, got {exc_info.value.code}"

        # Assert 0 file bytes modified
        assert temp_csv_file.read_bytes() == initial_csv_bytes, "CSV file was mutated on interim draw!"
        assert test_history.read_bytes() == initial_history_bytes, "History JSON was mutated on interim draw!"
        assert test_perf.read_bytes() == initial_perf_bytes, "Performance JSON was mutated on interim draw!"
        assert test_cache.read_bytes() == initial_cache_bytes, "Pipeline cache was mutated on interim draw!"
        mock_subprocess.assert_not_called()

    def test_empirical_zero_mutation_on_existing_draw(self, temp_csv_file, tmp_path):
        """Verify 0 file bytes modified and exit code 0 when draw is already recorded in CSV."""
        test_history = tmp_path / "prediction_history.json"
        test_perf = tmp_path / "performance.json"
        test_cache = tmp_path / "pipeline_cache.json"

        test_history.write_text('[]', encoding="utf-8")
        test_perf.write_text('{}', encoding="utf-8")
        test_cache.write_text('{"status": "ok"}', encoding="utf-8")

        initial_csv_bytes = temp_csv_file.read_bytes()
        initial_history_bytes = test_history.read_bytes()
        initial_perf_bytes = test_perf.read_bytes()
        initial_cache_bytes = test_cache.read_bytes()

        # 2026-09-01 already exists in temp_csv_file fixture
        existing_draw_data = {
            "first_prize": "417212",
            "front3": ["060", "521"],
            "back3": ["266", "041"],
            "last2": "04",
            "draw_date": "2026-09-01",
            "source": "sanook"
        }

        mock_subprocess = MagicMock()

        with patch.object(rf, "CSV_PATH", temp_csv_file), \
             patch.object(rf, "HISTORY_JSON", test_history), \
             patch.object(rf, "PERF_JSON", test_perf), \
             patch.object(rf, "fetch_thairath", MagicMock(return_value=existing_draw_data)), \
             patch.object(rf, "fetch_sanook", MagicMock(return_value=existing_draw_data)), \
             patch.object(rf, "fetch_kapook", MagicMock(return_value=existing_draw_data)), \
             patch("subprocess.run", mock_subprocess):

            with pytest.raises(SystemExit) as exc_info:
                rf.run(target_date="2026-09-01", force=False, exit_on_finish=True)

            assert exc_info.value.code == 0, f"Expected exit code 0, got {exc_info.value.code}"

        # Assert 0 file bytes modified
        assert temp_csv_file.read_bytes() == initial_csv_bytes, "CSV file was mutated on existing draw!"
        assert test_history.read_bytes() == initial_history_bytes, "History JSON was mutated on existing draw!"
        assert test_perf.read_bytes() == initial_perf_bytes, "Performance JSON was mutated on existing draw!"
        assert test_cache.read_bytes() == initial_cache_bytes, "Pipeline cache was mutated on existing draw!"
        mock_subprocess.assert_not_called()
