import pytest
import os
import json
import csv
from datetime import date
from app.models.lottery_draw import LotteryDraw
from app.datasets.dataset_builder import DatasetBuilder
from app.datasets.dataset_splitter import DatasetSplitter
from app.datasets.dataset_exporter import DatasetExporter

@pytest.fixture
def sample_draws():
    return [
        LotteryDraw(id=1, draw_date=date(2023, 1, 1), last_two="10"),
        LotteryDraw(id=2, draw_date=date(2023, 2, 1), last_two="20"),
        LotteryDraw(id=3, draw_date=date(2023, 3, 1), last_two="30"),
        LotteryDraw(id=4, draw_date=date(2023, 4, 1), last_two="40"),
        LotteryDraw(id=5, draw_date=date(2023, 5, 1), last_two="50")
    ]

def test_dataset_builder(sample_draws):
    builder = DatasetBuilder(sample_draws)
    # Use min_history=3, so it generates rows for draws 4 and 5 (indices 3 and 4)
    dataset = builder.build_dataset(min_history=3)
    
    # 2 draws * 100 candidates = 200 rows
    assert len(dataset) == 200
    
    # Target draw index 3 has last_two "40"
    # Target draw index 4 has last_two "50"
    
    # Check the labels for draw index 3
    draw_3_rows = [row for row in dataset if row["draw_date"] == "2023-04-01"]
    assert len(draw_3_rows) == 100
    
    winning_row_3 = next(r for r in draw_3_rows if r["candidate"] == "40")
    assert winning_row_3["label"] == 1
    
    losing_row_3 = next(r for r in draw_3_rows if r["candidate"] == "10")
    assert losing_row_3["label"] == 0
    
    # Check history dependency (gap for "10" at draw 4 should be calculated based on draws 1,2,3)
    # History for draw index 3 is ["10", "20", "30"]
    # So "10" has gap_since_last = 1 ("30" -> 0, "20" -> 1, "10" -> 2)
    # wait, reverse is ["30", "20", "10"], index of "10" is 2.
    assert losing_row_3["gap_since_last"] == 2

def test_dataset_splitter(sample_draws):
    builder = DatasetBuilder(sample_draws)
    dataset = builder.build_dataset(min_history=1) # 4 draws * 100 = 400 rows
    
    # We have 4 unique draw_dates
    # 4 draws. Ratios: 0.5, 0.25, 0.25
    # train = 2 draws, val = 1 draw, test = 1 draw
    train_set, val_set, test_set = DatasetSplitter.split(dataset, train_ratio=0.5, val_ratio=0.25, test_ratio=0.25)
    
    assert len(train_set) == 200
    assert len(val_set) == 100
    assert len(test_set) == 100
    
    # Check no draw_date overlaps
    train_dates = set(r["draw_date"] for r in train_set)
    val_dates = set(r["draw_date"] for r in val_set)
    test_dates = set(r["draw_date"] for r in test_set)
    
    assert len(train_dates.intersection(val_dates)) == 0
    assert len(val_dates.intersection(test_dates)) == 0

def test_dataset_exporter(tmp_path):
    dataset = [
        {"draw_date": "2023-01-01", "candidate": "10", "label": 1, "feature1": 5.0, "feature2": None},
        {"draw_date": "2023-01-01", "candidate": "11", "label": 0, "feature1": 2.0, "feature2": 1.0}
    ]
    
    csv_path = tmp_path / "test.csv"
    DatasetExporter.export_csv(dataset, str(csv_path))
    assert csv_path.exists()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["label"] == "1"
        assert rows[0]["feature2"] == ""
        
    json_path = tmp_path / "test.json"
    DatasetExporter.export_json(dataset, str(json_path))
    assert json_path.exists()
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert len(data) == 2
        assert data[0]["label"] == 1
        assert data[0]["feature2"] is None

def test_dataset_metadata():
    dataset = [
        {"draw_date": "2023-01-01", "candidate": "10", "label": 1, "feature1": 5.0, "feature2": None},
        {"draw_date": "2023-01-01", "candidate": "11", "label": 0, "feature1": 2.0, "feature2": 1.0}
    ]
    
    meta = DatasetExporter.generate_metadata(dataset)
    assert meta["total_samples"] == 2
    assert meta["feature_count"] == 2 # feature1, feature2
    assert meta["target_columns"] == ["label"]
    assert meta["missing_values"]["feature2"] == 1
    assert "generated_timestamp" in meta
