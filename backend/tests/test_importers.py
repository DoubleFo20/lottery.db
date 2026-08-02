import pytest
import os
import csv
import json
from importers.csv_importer import CSVImporter
from importers.json_importer import JSONImporter
from importers.future_web_importer import WebImporter

def test_csv_importer(tmp_path):
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["draw_date", "first_prize", "last_two", "front_three", "back_three"])
        writer.writerow(["2023-10-01", "123456", "78", "123", "456"])
        writer.writerow(["2023-10-16", " 654321 ", "", "  ", None])

    importer = CSVImporter()
    results = importer.parse(str(csv_file))
    
    assert len(results) == 2
    assert results[0]["draw_date"] == "2023-10-01"
    assert results[0]["first_prize"] == "123456"
    assert results[1]["draw_date"] == "2023-10-16"
    assert results[1]["first_prize"] == "654321"
    assert results[1]["last_two"] is None
    assert results[1]["front_three"] is None

def test_json_importer(tmp_path):
    json_file = tmp_path / "test.json"
    data = [
        {"draw_date": "2023-10-01", "first_prize": "123456", "last_two": "78", "front_three": "123", "back_three": "456"},
        {"draw_date": "2023-10-16", "first_prize": 654321, "last_two": None, "front_three": "", "back_three": None}
    ]
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
        
    importer = JSONImporter()
    results = importer.parse(str(json_file))
    
    assert len(results) == 2
    assert results[0]["first_prize"] == "123456"
    assert results[1]["first_prize"] == "654321"
    assert results[1]["last_two"] is None
    assert results[1]["front_three"] is None

def test_web_importer_not_implemented():
    importer = WebImporter()
    with pytest.raises(NotImplementedError):
        importer.parse()
