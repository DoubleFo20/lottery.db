"""tests/test_result_fetcher.py
Comprehensive test suite for analytics/result_fetcher.py across Tiers 1-4:
- Tier 1: Feature Coverage (Date resolution, 6-digit first prize, 2-digit last 2, consensus, CSV append)
- Tier 2: Boundary & Corner Cases (Rejection of placeholders, waiting text, incomplete lengths, older/future dates)
- Tier 3: Cross-Feature Combinations (Pairwise interactions, clean exit 0, zero mutations on existing/incomplete)
- Tier 4: Real-World Workload Scenarios (Full draw day polling lifecycle: unannounced -> interim -> complete -> subsequent runs)
"""

import csv
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

import analytics.result_fetcher as rf


# =====================================================================
# TIER 1: FEATURE COVERAGE (HAPPY-PATH ISOLATION)
# =====================================================================

class TestTier1FeatureCoverage:
    """Tier 1: Systematic happy-path coverage for core feature functions."""

    # ── Feature 1: Expected Draw Date Resolution ─────────────────────

    def test_tier1_draw_date_on_1st_of_standard_month(self):
        """Standard 1st of the month (e.g. 2026-06-01) resolves to itself."""
        ref = date(2026, 6, 1)
        assert rf.is_draw_day(ref) is True
        assert rf.get_expected_draw_date(ref) == "2026-06-01"

    def test_tier1_draw_date_on_16th_of_standard_month(self):
        """Standard 16th of the month (e.g. 2026-09-16) resolves to itself."""
        ref = date(2026, 9, 16)
        assert rf.is_draw_day(ref) is True
        assert rf.get_expected_draw_date(ref) == "2026-09-16"

    def test_tier1_draw_date_on_labour_day_shift_may_2(self):
        """May 1 is Labour Day; draw moves to May 2."""
        may1 = date(2026, 5, 1)
        may2 = date(2026, 5, 2)
        assert rf.is_draw_day(may1) is False
        assert rf.is_draw_day(may2) is True
        assert rf.get_expected_draw_date(may2) == "2026-05-02"

    def test_tier1_draw_date_on_teachers_day_shift_jan_17(self):
        """Jan 16 is Teacher's Day; draw moves to Jan 17."""
        jan16 = date(2026, 1, 16)
        jan17 = date(2026, 1, 17)
        assert rf.is_draw_day(jan16) is False
        assert rf.is_draw_day(jan17) is True
        assert rf.get_expected_draw_date(jan17) == "2026-01-17"

    def test_tier1_draw_date_on_new_year_shift_dec_30(self):
        """Jan 1 is New Year; draw moves to Dec 30 of preceding year."""
        jan1 = date(2026, 1, 1)
        dec30 = date(2026, 12, 30)
        assert rf.is_draw_day(jan1) is False
        assert rf.is_draw_day(dec30) is True
        assert rf.get_expected_draw_date(dec30) == "2026-12-30"

    def test_tier1_draw_date_on_non_draw_day_resolves_to_latest_past_draw(self):
        """On a non-draw day (e.g. Sep 20), resolves to the latest passed draw date (Sep 16)."""
        ref = date(2026, 9, 20)
        assert rf.is_draw_day(ref) is False
        assert rf.get_expected_draw_date(ref) == "2026-09-16"

    # ── Feature 2: Strict 6-Digit First Prize Validation ─────────────

    def test_tier1_valid_6digit_first_prize_standard(self):
        """Standard 6-digit numeric prize string is accepted."""
        result = {"first_prize": "730640", "last2": "64", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is True

    def test_tier1_valid_6digit_first_prize_with_leading_zeros(self):
        """6-digit prize with leading zeros (e.g. '001234') is valid."""
        result = {"first_prize": "001234", "last2": "56", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is True

    def test_tier1_valid_6digit_first_prize_all_zeros(self):
        """Boundary number '000000' is a valid 6-digit numeric string."""
        result = {"first_prize": "000000", "last2": "00", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is True

    def test_tier1_valid_6digit_first_prize_all_nines(self):
        """Boundary number '999999' is a valid 6-digit numeric string."""
        result = {"first_prize": "999999", "last2": "99", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is True

    def test_tier1_valid_6digit_first_prize_complete_with_auxiliary(self):
        """Full draw payload with front3 and back3 auxiliary prizes is valid."""
        result = {
            "first_prize": "730640",
            "front3": ["060", "521"],
            "back3": ["266", "041"],
            "last2": "64",
            "draw_date": "2026-09-16",
            "source": "sanook"
        }
        assert rf.is_valid_draw_result(result, "2026-09-16") is True

    # ── Feature 3: Strict 2-Digit Last 2 Digits Validation ───────────

    def test_tier1_valid_last2_double_digits(self):
        """Standard 2-digit number (e.g. '88') is valid."""
        result = {"first_prize": "123456", "last2": "88", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is True

    def test_tier1_valid_last2_leading_zero(self):
        """Last 2 with leading zero (e.g. '07') is valid."""
        result = {"first_prize": "123456", "last2": "07", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is True

    def test_tier1_valid_last2_zero_zero(self):
        """Last 2 boundary '00' is valid."""
        result = {"first_prize": "123456", "last2": "00", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is True

    def test_tier1_valid_last2_nine_nine(self):
        """Last 2 boundary '99' is valid."""
        result = {"first_prize": "123456", "last2": "99", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is True

    def test_tier1_valid_last2_exact_type_check(self):
        """Validation accepts valid integers if converted to string or string input."""
        result = {"first_prize": "654321", "last2": "42", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is True

    # ── Feature 4: Consensus Resolution ──────────────────────────────

    def test_tier1_consensus_unanimous_three_sources(self):
        """Consensus succeeds when all 3 scrapers return identical winning numbers."""
        mock_thairath = MagicMock(return_value={
            "first_prize": "730640", "last2": "64", "draw_date": "2026-09-16",
            "front3": ["060", "521"], "back3": ["266", "041"], "source": "thairath"
        })
        mock_sanook = MagicMock(return_value={
            "first_prize": "730640", "last2": "64", "draw_date": "2026-09-16",
            "front3": ["060", "521"], "back3": ["266", "041"], "source": "sanook"
        })
        mock_kapook = MagicMock(return_value={
            "first_prize": "730640", "last2": "64", "draw_date": "2026-09-16",
            "front3": ["060", "521"], "back3": ["266", "041"], "source": "kapook"
        })

        with patch.object(rf, "fetch_thairath", mock_thairath), \
             patch.object(rf, "fetch_sanook", mock_sanook), \
             patch.object(rf, "fetch_kapook", mock_kapook):
            res = rf.collect_and_validate("2026-09-16")
            assert res is not None
            assert res["first_prize"] == "730640"
            assert res["last2"] == "64"
            assert res["draw_date"] == "2026-09-16"

    def test_tier1_consensus_two_of_three_sources_agree(self):
        """Consensus succeeds when 2 sources match, even if 1 source fails or has old draw."""
        # Thairath has prior draw (Sep 1), Sanook and Kapook have Sep 16
        mock_thairath = MagicMock(return_value={
            "first_prize": "417212", "last2": "04", "draw_date": "2026-09-01",
            "front3": ["060", "521"], "back3": ["266", "041"], "source": "thairath"
        })
        mock_sanook = MagicMock(return_value={
            "first_prize": "730640", "last2": "64", "draw_date": "2026-09-16",
            "front3": ["060", "521"], "back3": ["266", "041"], "source": "sanook"
        })
        mock_kapook = MagicMock(return_value={
            "first_prize": "730640", "last2": "64", "draw_date": "2026-09-16",
            "front3": ["060", "521"], "back3": ["266", "041"], "source": "kapook"
        })

        with patch.object(rf, "fetch_thairath", mock_thairath), \
             patch.object(rf, "fetch_sanook", mock_sanook), \
             patch.object(rf, "fetch_kapook", mock_kapook):
            res = rf.collect_and_validate("2026-09-16")
            assert res is not None
            assert res["first_prize"] == "730640"
            assert res["last2"] == "64"
            assert "sanook" in res["source"] and "kapook" in res["source"]

    def test_tier1_consensus_selects_source_with_richest_auxiliary_data(self):
        """When matching sources have identical 1st and last2, prefers one with complete front/back3."""
        mock_sanook = MagicMock(return_value={
            "first_prize": "730640", "last2": "64", "draw_date": "2026-09-16",
            "front3": ["060", "521"], "back3": ["266", "041"], "source": "sanook"
        })
        mock_kapook = MagicMock(return_value={
            "first_prize": "730640", "last2": "64", "draw_date": "2026-09-16",
            "front3": ["", ""], "back3": ["", ""], "source": "kapook"
        })

        with patch.object(rf, "fetch_thairath", MagicMock(return_value=None)), \
             patch.object(rf, "fetch_sanook", mock_sanook), \
             patch.object(rf, "fetch_kapook", mock_kapook):
            res = rf.collect_and_validate("2026-09-16")
            assert res is not None
            assert res["front3"] == ["060", "521"]
            assert res["back3"] == ["266", "041"]

    def test_tier1_consensus_disagreement_between_sources_fails(self):
        """Consensus fails (returns None) if all 3 sources provide different numbers."""
        mock_thairath = MagicMock(return_value={
            "first_prize": "111111", "last2": "11", "draw_date": "2026-09-16", "source": "thairath"
        })
        mock_sanook = MagicMock(return_value={
            "first_prize": "222222", "last2": "22", "draw_date": "2026-09-16", "source": "sanook"
        })
        mock_kapook = MagicMock(return_value={
            "first_prize": "333333", "last2": "33", "draw_date": "2026-09-16", "source": "kapook"
        })

        with patch.object(rf, "fetch_thairath", mock_thairath), \
             patch.object(rf, "fetch_sanook", mock_sanook), \
             patch.object(rf, "fetch_kapook", mock_kapook):
            res = rf.collect_and_validate("2026-09-16")
            assert res is None

    def test_tier1_consensus_single_source_only_fails_threshold(self):
        """Consensus fails when only 1 source returns valid data (minimum required: 2)."""
        mock_sanook = MagicMock(return_value={
            "first_prize": "730640", "last2": "64", "draw_date": "2026-09-16", "source": "sanook"
        })

        with patch.object(rf, "fetch_thairath", MagicMock(return_value=None)), \
             patch.object(rf, "fetch_sanook", mock_sanook), \
             patch.object(rf, "fetch_kapook", MagicMock(return_value=None)):
            res = rf.collect_and_validate("2026-09-16")
            assert res is None

    # ── Feature 5: CSV Append & Chronological Descending Order ───────

    def test_tier1_csv_append_new_draw_top_of_file(self, temp_csv_file, sample_valid_draw):
        """Verified new draw is prepended to the top of lottery_history.csv."""
        with patch.object(rf, "CSV_PATH", temp_csv_file):
            success = rf.append_dataset(sample_valid_draw)
            assert success is True

            with open(temp_csv_file, "r", encoding="utf-8") as f:
                reader = list(csv.DictReader(f))

            assert len(reader) == 4  # Was 3, now 4
            assert reader[0]["draw_date"] == "2026-09-16"
            assert reader[0]["first_prize"] == "730640"
            assert reader[0]["last2"] == "64"

    def test_tier1_csv_append_preserves_all_13_columns(self, temp_csv_file, sample_valid_draw):
        """Verify that all 13 standard CSV columns are present and correctly populated."""
        with patch.object(rf, "CSV_PATH", temp_csv_file):
            rf.append_dataset(sample_valid_draw)

            with open(temp_csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                header = reader.fieldnames
                first_row = next(reader)

            expected_header = [
                "draw_date", "first_prize",
                "front3_1", "front3_2", "back3_1", "back3_2", "last2",
                "digit1", "digit2", "digit3", "digit4", "digit5", "digit6"
            ]
            assert header == expected_header
            assert first_row["front3_1"] == "060"
            assert first_row["front3_2"] == "521"
            assert first_row["back3_1"] == "266"
            assert first_row["back3_2"] == "041"

    def test_tier1_csv_append_digit_decomposition_exact(self, temp_csv_file, sample_valid_draw):
        """Verify first prize '730640' is cleanly decomposed into digit1..digit6."""
        with patch.object(rf, "CSV_PATH", temp_csv_file):
            rf.append_dataset(sample_valid_draw)

            with open(temp_csv_file, "r", encoding="utf-8") as f:
                row = next(csv.DictReader(f))

            assert [row[f"digit{i}"] for i in range(1, 7)] == ["7", "3", "0", "6", "4", "0"]

    def test_tier1_csv_append_past_date_inserted_in_sorted_order(self, temp_csv_file):
        """Inserting an older missing date (e.g. 2026-08-08) preserves strict descending sort."""
        past_draw = {
            "first_prize": "555555",
            "front3": ["111", "222"],
            "back3": ["333", "444"],
            "last2": "55",
            "draw_date": "2026-08-08",
            "source": "manual"
        }
        with patch.object(rf, "CSV_PATH", temp_csv_file):
            success = rf.append_dataset(past_draw)
            assert success is True

            with open(temp_csv_file, "r", encoding="utf-8") as f:
                dates = [row["draw_date"] for row in csv.DictReader(f)]

            # Check descending order: 2026-09-01, 2026-08-16, 2026-08-08, 2026-08-01
            assert dates == ["2026-09-01", "2026-08-16", "2026-08-08", "2026-08-01"]

    def test_tier1_csv_append_returns_true_on_success(self, temp_csv_file, sample_valid_draw):
        """append_dataset returns boolean True on successful record creation."""
        with patch.object(rf, "CSV_PATH", temp_csv_file):
            res = rf.append_dataset(sample_valid_draw)
            assert res is True


# =====================================================================
# TIER 2: BOUNDARY & CORNER CASES (REJECTION & BVA)
# =====================================================================

class TestTier2BoundaryAndCornerCases:
    """Tier 2: Boundary Value Analysis, placeholder strings, waiting text, and invalid inputs."""

    # ── Boundary Set 1: Rejection of Placeholder Strings ─────────────

    @pytest.mark.parametrize("placeholder", ["--", "---", "----", "------", "-"])
    def test_tier2_reject_dashes_first_prize(self, placeholder):
        """Reject First Prize containing dashes."""
        result = {"first_prize": placeholder, "last2": "64", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    @pytest.mark.parametrize("placeholder", ["--", "---", "-"])
    def test_tier2_reject_dashes_last2(self, placeholder):
        """Reject Last 2 containing dashes."""
        result = {"first_prize": "730640", "last2": placeholder, "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    @pytest.mark.parametrize("placeholder", ["..", "...", "......"])
    def test_tier2_reject_dots_first_prize_and_last2(self, placeholder):
        """Reject dots used as live draw placeholders."""
        assert rf.is_valid_draw_result({"first_prize": placeholder, "last2": "64", "draw_date": "2026-09-16"}, "2026-09-16") is False
        assert rf.is_valid_draw_result({"first_prize": "730640", "last2": placeholder, "draw_date": "2026-09-16"}, "2026-09-16") is False

    @pytest.mark.parametrize("placeholder", ["XXXXXX", "xxxxxx", "XXX", "X"])
    def test_tier2_reject_x_placeholders(self, placeholder):
        """Reject 'X' placeholders commonly used in news tickers."""
        assert rf.is_valid_draw_result({"first_prize": placeholder, "last2": "64", "draw_date": "2026-09-16"}, "2026-09-16") is False
        assert rf.is_valid_draw_result({"first_prize": "730640", "last2": placeholder, "draw_date": "2026-09-16"}, "2026-09-16") is False

    @pytest.mark.parametrize("waiting_text", ["รอผล", "รอผลรางวัล", "รอยืนยัน", "รอการออกรางวัล", "กำลังออกผล"])
    def test_tier2_reject_thai_waiting_text(self, waiting_text):
        """Reject Thai waiting phrases appearing during broadcast delays."""
        assert rf.is_valid_draw_result({"first_prize": waiting_text, "last2": "64", "draw_date": "2026-09-16"}, "2026-09-16") is False
        assert rf.is_valid_draw_result({"first_prize": "730640", "last2": waiting_text, "draw_date": "2026-09-16"}, "2026-09-16") is False

    # ── Boundary Set 2: Incomplete Lengths & Format Inadequacy ────────

    @pytest.mark.parametrize("short_fp", ["", "1", "12", "123", "1234", "12345"])
    def test_tier2_reject_short_first_prize(self, short_fp):
        """First prize strictly requires exactly 6 digits; shorter lengths rejected."""
        result = {"first_prize": short_fp, "last2": "64", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    @pytest.mark.parametrize("long_fp", ["1234567", "12345678", "7306401"])
    def test_tier2_reject_long_first_prize(self, long_fp):
        """First prize longer than 6 digits rejected."""
        result = {"first_prize": long_fp, "last2": "64", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    @pytest.mark.parametrize("invalid_last2", ["", "6", "640", "6400", "   "])
    def test_tier2_reject_incorrect_length_last2(self, invalid_last2):
        """Last 2 strictly requires exactly 2 digits."""
        result = {"first_prize": "730640", "last2": invalid_last2, "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    @pytest.mark.parametrize("non_numeric", ["73064A", "73-640", "73 640", "7306.0", "#30640"])
    def test_tier2_reject_non_numeric_first_prize(self, non_numeric):
        """Any non-digit character in first prize is rejected."""
        result = {"first_prize": non_numeric, "last2": "64", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    def test_tier2_reject_none_or_empty_result(self):
        """Reject None, empty dictionary, or non-dict payloads."""
        assert rf.is_valid_draw_result(None, "2026-09-16") is False
        assert rf.is_valid_draw_result({}, "2026-09-16") is False
        assert rf.is_valid_draw_result("invalid", "2026-09-16") is False

    # ── Boundary Set 3: Date Boundary Rejection ──────────────────────

    def test_tier2_reject_older_draw_date(self):
        """Reject valid prize results if date belongs to a previous draw (e.g. Sep 1 when target is Sep 16)."""
        result = {"first_prize": "417212", "last2": "04", "draw_date": "2026-09-01"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    def test_tier2_reject_future_unannounced_date(self):
        """Reject draw dates ahead of target draw schedule."""
        result = {"first_prize": "730640", "last2": "64", "draw_date": "2026-10-01"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    @pytest.mark.parametrize("malformed_date", ["16/09/2026", "2026/09/16", "2026-9-16", "not-a-date", ""])
    def test_tier2_reject_malformed_draw_date_strings(self, malformed_date):
        """Reject non-ISO or malformed date representations."""
        result = {"first_prize": "730640", "last2": "64", "draw_date": malformed_date}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False


# =====================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (PAIRWISE & IDEMPOTENCY)
# =====================================================================

class TestTier3CrossFeatureCombinations:
    """Tier 3: Feature interactions, edge combinations, clean exit code 0, and zero-mutation checks."""

    def test_tier3_date_match_with_incomplete_first_prize(self):
        """Date matches target, but First Prize is placeholder -> Rejected."""
        result = {"first_prize": "------", "last2": "64", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    def test_tier3_date_match_with_incomplete_last2(self):
        """Date matches target, First Prize is valid, but Last 2 is placeholder -> Rejected."""
        result = {"first_prize": "730640", "last2": "--", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    def test_tier3_date_match_with_empty_last2(self):
        """Date matches target, First Prize valid, but Last 2 empty string -> Rejected."""
        result = {"first_prize": "730640", "last2": "", "draw_date": "2026-09-16"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    def test_tier3_date_mismatch_with_fully_valid_prizes(self):
        """Both First Prize and Last 2 are valid numeric strings, but date mismatches -> Rejected."""
        result = {"first_prize": "417212", "last2": "04", "draw_date": "2026-09-01"}
        assert rf.is_valid_draw_result(result, "2026-09-16") is False

    def test_tier3_existing_date_in_csv_clean_exit_0_without_file_mutations(self, temp_csv_file):
        """
        When target draw date already exists in CSV:
        - append_dataset returns False
        - CSV file content, size, and line count remain 100% identical
        - run() exits cleanly (or returns False if exit_on_finish=False)
        - Subprocess retrain pipeline is NOT called
        """
        # 2026-09-01 already exists in temp_csv_file
        existing_result = {
            "first_prize": "417212",
            "front3": ["060", "521"],
            "back3": ["266", "041"],
            "last2": "04",
            "draw_date": "2026-09-01",
            "source": "sanook"
        }

        # Read original CSV bytes
        original_bytes = temp_csv_file.read_bytes()

        with patch.object(rf, "CSV_PATH", temp_csv_file):
            appended = rf.append_dataset(existing_result)
            assert appended is False
            # Verify ZERO file mutations
            assert temp_csv_file.read_bytes() == original_bytes

        # Now test run() with mocked collection
        mock_collect = MagicMock(return_value=existing_result)
        mock_subprocess = MagicMock()

        with patch.object(rf, "CSV_PATH", temp_csv_file), \
             patch.object(rf, "collect_and_validate", mock_collect), \
             patch("subprocess.run", mock_subprocess):

            # exit_on_finish=False enables inspecting return value
            success = rf.run(target_date="2026-09-01", force=False, exit_on_finish=False)
            assert success is False
            # Subprocess must NOT have been called
            mock_subprocess.assert_not_called()
            # File still untouched
            assert temp_csv_file.read_bytes() == original_bytes

    def test_tier3_clean_exit_zero_via_sys_exit(self, temp_csv_file):
        """Verify that when exit_on_finish=True, sys.exit(0) is cleanly invoked on existing draw."""
        existing_result = {
            "first_prize": "417212",
            "front3": ["060", "521"],
            "back3": ["266", "041"],
            "last2": "04",
            "draw_date": "2026-09-01",
            "source": "sanook"
        }
        with patch.object(rf, "CSV_PATH", temp_csv_file), \
             patch.object(rf, "collect_and_validate", MagicMock(return_value=existing_result)):

            with pytest.raises(SystemExit) as exc_info:
                rf.run(target_date="2026-09-01", force=False, exit_on_finish=True)
            assert exc_info.value.code == 0

    def test_tier3_network_failure_all_scrapers_clean_exit_0(self, temp_csv_file):
        """
        When all scrapers return None (e.g. network timeout or 503 error):
        - collect_and_validate returns None
        - run() exits with code 0 without raising exception
        - No files modified
        """
        original_bytes = temp_csv_file.read_bytes()
        with patch.object(rf, "CSV_PATH", temp_csv_file), \
             patch.object(rf, "collect_and_validate", MagicMock(return_value=None)):

            with pytest.raises(SystemExit) as exc_info:
                rf.run(target_date="2026-09-16", exit_on_finish=True)
            assert exc_info.value.code == 0
            assert temp_csv_file.read_bytes() == original_bytes

    def test_tier3_consensus_with_one_valid_and_one_placeholder_source(self):
        """One source has valid numbers, second source has placeholders -> No consensus (< 2 valid)."""
        mock_sanook = MagicMock(return_value={
            "first_prize": "730640", "last2": "64", "draw_date": "2026-09-16", "source": "sanook"
        })
        mock_kapook = MagicMock(return_value={
            "first_prize": "------", "last2": "--", "draw_date": "2026-09-16", "source": "kapook"
        })

        with patch.object(rf, "fetch_thairath", MagicMock(return_value=None)), \
             patch.object(rf, "fetch_sanook", mock_sanook), \
             patch.object(rf, "fetch_kapook", mock_kapook):
            res = rf.collect_and_validate("2026-09-16")
            assert res is None


# =====================================================================
# TIER 4: REAL-WORLD WORKLOAD SCENARIOS (LIFECYCLE SIMULATION)
# =====================================================================

class TestTier4RealWorldWorkloadScenarios:
    """
    Tier 4: End-to-end simulation of a complete draw day lifecycle:
    14:30 (Unannounced) -> 15:00 (Interim) -> 15:45 (Final verified) -> 16:00 (Subsequent run)
    """

    def test_tier4_full_draw_day_lifecycle_simulation(self, temp_csv_file):
        """
        Simulate 4 consecutive 15-minute cron poll runs on 2026-09-16:
        - Run 1 (14:30 ICT): Draw unannounced. Scrapers show placeholders. -> Clean exit 0, 0 mutations.
        - Run 2 (15:00 ICT): Interim state. Last 2 drawn ('64'), but First Prize is '------'. -> Clean exit 0, 0 mutations.
        - Run 3 (15:45 ICT): Final verified! First Prize '730640' and Last 2 '64'. -> CSV appended, pipeline retrained.
        - Run 4 (16:00 ICT): Subsequent run. Same data on websites. -> Already exists, Clean exit 0, 0 mutations, NO retrain.
        """
        target_date = "2026-09-16"
        initial_bytes = temp_csv_file.read_bytes()

        # ── RUN 1: 14:30 ICT — All sources show placeholders ───────────
        run1_mock_data = {
            "first_prize": "------",
            "front3": ["---", "---"],
            "back3": ["---", "---"],
            "last2": "--",
            "draw_date": target_date,
            "source": "sanook"
        }
        with patch.object(rf, "CSV_PATH", temp_csv_file), \
             patch.object(rf, "fetch_thairath", MagicMock(return_value=None)), \
             patch.object(rf, "fetch_sanook", MagicMock(return_value=run1_mock_data)), \
             patch.object(rf, "fetch_kapook", MagicMock(return_value=run1_mock_data)):

            # Run 1 execution
            r1_result = rf.run(target_date=target_date, exit_on_finish=False)
            assert r1_result is False
            assert temp_csv_file.read_bytes() == initial_bytes, "Run 1 must not modify CSV"

        # ── RUN 2: 15:00 ICT — Interim: Last 2 drawn, First Prize pending ─
        run2_mock_data = {
            "first_prize": "------",
            "front3": ["060", "521"],
            "back3": ["266", "041"],
            "last2": "64",
            "draw_date": target_date,
            "source": "sanook"
        }
        with patch.object(rf, "CSV_PATH", temp_csv_file), \
             patch.object(rf, "fetch_thairath", MagicMock(return_value=None)), \
             patch.object(rf, "fetch_sanook", MagicMock(return_value=run2_mock_data)), \
             patch.object(rf, "fetch_kapook", MagicMock(return_value=run2_mock_data)):

            # Run 2 execution
            r2_result = rf.run(target_date=target_date, exit_on_finish=False)
            assert r2_result is False
            assert temp_csv_file.read_bytes() == initial_bytes, "Run 2 must not modify CSV"

        # ── RUN 3: 15:45 ICT — Final verified: Both 1st and Last 2 announced ─
        run3_sanook = {
            "first_prize": "730640",
            "front3": ["060", "521"],
            "back3": ["266", "041"],
            "last2": "64",
            "draw_date": target_date,
            "source": "sanook"
        }
        run3_kapook = {
            "first_prize": "730640",
            "front3": ["060", "521"],
            "back3": ["266", "041"],
            "last2": "64",
            "draw_date": target_date,
            "source": "kapook"
        }
        # Thairath still shows old archive draw (Sep 1)
        run3_thairath = {
            "first_prize": "417212",
            "front3": ["060", "521"],
            "back3": ["266", "041"],
            "last2": "04",
            "draw_date": "2026-09-01",
            "source": "thairath"
        }

        mock_subprocess = MagicMock()
        with patch.object(rf, "CSV_PATH", temp_csv_file), \
             patch.object(rf, "fetch_thairath", MagicMock(return_value=run3_thairath)), \
             patch.object(rf, "fetch_sanook", MagicMock(return_value=run3_sanook)), \
             patch.object(rf, "fetch_kapook", MagicMock(return_value=run3_kapook)), \
             patch.object(rf, "update_metrics", MagicMock()), \
             patch("subprocess.run", mock_subprocess):

            # Run 3 execution
            r3_result = rf.run(target_date=target_date, exit_on_finish=False)
            assert r3_result is True, "Run 3 must succeed on verified draw"
            mock_subprocess.assert_called_once()

            # Verify CSV was mutated with the new row at top
            with open(temp_csv_file, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == 4
            assert rows[0]["draw_date"] == target_date
            assert rows[0]["first_prize"] == "730640"

        # Capture state after Run 3
        post_run3_bytes = temp_csv_file.read_bytes()

        # ── RUN 4: 16:00 ICT — Subsequent run (Idempotency check) ─────
        mock_subprocess_run4 = MagicMock()
        with patch.object(rf, "CSV_PATH", temp_csv_file), \
             patch.object(rf, "fetch_thairath", MagicMock(return_value=run3_sanook)), \
             patch.object(rf, "fetch_sanook", MagicMock(return_value=run3_sanook)), \
             patch.object(rf, "fetch_kapook", MagicMock(return_value=run3_kapook)), \
             patch("subprocess.run", mock_subprocess_run4):

            # Run 4 execution
            r4_result = rf.run(target_date=target_date, exit_on_finish=False)
            assert r4_result is False, "Run 4 must exit cleanly without re-appending"
            mock_subprocess_run4.assert_not_called()
            assert temp_csv_file.read_bytes() == post_run3_bytes, "Run 4 must not mutate CSV"

    def test_tier4_dataset_integrity_across_multiple_draw_cycles(self, tmp_path):
        """Simulate sequential monthly draw cycles into an empty dataset preserving sort and unique constraints."""
        csv_file = tmp_path / "multi_cycle.csv"
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "draw_date", "first_prize",
                "front3_1", "front3_2", "back3_1", "back3_2", "last2",
                "digit1", "digit2", "digit3", "digit4", "digit5", "digit6"
            ])
            writer.writeheader()

        with patch.object(rf, "CSV_PATH", csv_file):
            draws = [
                {"first_prize": "111111", "last2": "11", "draw_date": "2026-08-01", "front3": ["", ""], "back3": ["", ""]},
                {"first_prize": "222222", "last2": "22", "draw_date": "2026-08-16", "front3": ["", ""], "back3": ["", ""]},
                {"first_prize": "333333", "last2": "33", "draw_date": "2026-09-01", "front3": ["", ""], "back3": ["", ""]},
                {"first_prize": "444444", "last2": "44", "draw_date": "2026-09-16", "front3": ["", ""], "back3": ["", ""]},
            ]
            for d in draws:
                assert rf.append_dataset(d) is True

            # Attempt duplicate
            assert rf.append_dataset(draws[1]) is False

            with open(csv_file, "r", encoding="utf-8") as f:
                saved_dates = [row["draw_date"] for row in csv.DictReader(f)]

            assert saved_dates == ["2026-09-16", "2026-09-01", "2026-08-16", "2026-08-01"]
            assert len(saved_dates) == 4

    def test_tier4_github_output_environment_variable(self, tmp_path):
        """Verify set_github_output appends to $GITHUB_OUTPUT file properly."""
        gh_output = tmp_path / "github_output.txt"
        with patch.dict("os.environ", {"GITHUB_OUTPUT": str(gh_output)}):
            rf.set_github_output("has_new_draw", "true")
            assert gh_output.read_text(encoding="utf-8").strip() == "has_new_draw=true"

    def test_tier4_cli_invocation_invalid_date_exit_code_1(self):
        """CLI invocation with invalid date string exits with code 1."""
        import subprocess
        import sys
        cmd = [sys.executable, "analytics/result_fetcher.py", "--date", "2026-99-99"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(rf.BASE))
        assert res.returncode == 1
        assert "Invalid date format" in res.stdout or "Invalid date format" in res.stderr

    def test_tier4_cli_invocation_already_existing_date_exit_code_0(self):
        """CLI invocation with existing historical date exits cleanly with code 0."""
        import subprocess
        import sys
        # 2026-09-01 is in lottery_history.csv
        cmd = [sys.executable, "analytics/result_fetcher.py", "--date", "2026-09-01"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(rf.BASE))
        assert res.returncode == 0

