"""tests/conftest.py
Shared test fixtures for Lottery Auto-Update and Result Fetcher test suites.
"""

import csv
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_CSV_PATH = REPO_ROOT / "database" / "dataset" / "lottery_history.csv"


SAMPLE_CSV_HEADER = [
    "draw_date", "first_prize",
    "front3_1", "front3_2", "back3_1", "back3_2", "last2",
    "digit1", "digit2", "digit3", "digit4", "digit5", "digit6"
]

SAMPLE_CSV_ROWS = [
    {
        "draw_date": "2026-09-01",
        "first_prize": "417212",
        "front3_1": "060", "front3_2": "521",
        "back3_1": "266", "back3_2": "041",
        "last2": "04",
        "digit1": "4", "digit2": "1", "digit3": "7",
        "digit4": "2", "digit5": "1", "digit6": "2"
    },
    {
        "draw_date": "2026-08-16",
        "first_prize": "890456",
        "front3_1": "123", "front3_2": "456",
        "back3_1": "789", "back3_2": "012",
        "last2": "56",
        "digit1": "8", "digit2": "9", "digit3": "0",
        "digit4": "4", "digit5": "5", "digit6": "6"
    },
    {
        "draw_date": "2026-08-01",
        "first_prize": "123789",
        "front3_1": "111", "front3_2": "222",
        "back3_1": "333", "back3_2": "444",
        "last2": "89",
        "digit1": "1", "digit2": "2", "digit3": "3",
        "digit4": "7", "digit5": "8", "digit6": "9"
    }
]


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create an isolated temporary lottery_history.csv file."""
    csv_file = tmp_path / "lottery_history.csv"
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SAMPLE_CSV_HEADER)
        writer.writeheader()
        writer.writerows(SAMPLE_CSV_ROWS)
    return csv_file


@pytest.fixture
def sample_valid_draw():
    """Return a verified, complete draw dictionary."""
    return {
        "first_prize": "730640",
        "front3": ["060", "521"],
        "back3": ["266", "041"],
        "last2": "64",
        "draw_date": "2026-09-16",
        "source": "sanook"
    }


@pytest.fixture
def sample_interim_draw():
    """Return an interim draw dictionary (First Prize pending, Last2 ready)."""
    return {
        "first_prize": "------",
        "front3": ["060", "521"],
        "back3": ["266", "041"],
        "last2": "64",
        "draw_date": "2026-09-16",
        "source": "sanook"
    }


@pytest.fixture
def sample_unannounced_draw():
    """Return an unannounced draw dictionary with all placeholders."""
    return {
        "first_prize": "------",
        "front3": ["---", "---"],
        "back3": ["---", "---"],
        "last2": "--",
        "draw_date": "2026-09-16",
        "source": "sanook"
    }
