import pytest
import csv
from datetime import date
from sqlalchemy.orm import Session
from app.services.import_service import ImportService
from importers.csv_importer import CSVImporter
from app.repositories.lottery_draw import lottery_draw
from app.repositories.import_log import import_log
from app.models.lottery_draw import LotteryDraw
from app.models.import_log import ImportLog

def test_import_service_valid(db_session: Session, tmp_path):
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["draw_date", "first_prize", "last_two"])
        writer.writerow(["2023-11-01", "123456", "78"])
        writer.writerow(["2023-11-16", "654321", "90"])
        
    importer = CSVImporter()
    service = ImportService(db_session, importer)
    
    results = service.process_import(str(csv_file))
    
    assert results["total_rows"] == 2
    assert results["imported"] == 2
    assert results["rejected_invalid"] == 0
    assert results["skipped_duplicates"] == 0
    
    draws = db_session.query(LotteryDraw).all()
    assert len(draws) == 2
    
    logs = db_session.query(ImportLog).all()
    assert len(logs) == 1
    assert logs[0].status == "completed"
    assert logs[0].rows_imported == 2

def test_import_service_duplicates_skipped(db_session: Session, tmp_path):
    # Insert existing draw
    draw_in = LotteryDraw(
        draw_date=date(2023, 11, 1),
        first_prize="123456",
        source="csv"
    )
    db_session.add(draw_in)
    db_session.commit()

    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["draw_date", "first_prize", "last_two"])
        writer.writerow(["2023-11-01", "123456", "78"]) # duplicate
        writer.writerow(["2023-11-16", "654321", "90"]) # new
        
    importer = CSVImporter()
    service = ImportService(db_session, importer)
    results = service.process_import(str(csv_file))
    
    assert results["total_rows"] == 2
    assert results["imported"] == 1
    assert results["skipped_duplicates"] == 1
    
    draws = db_session.query(LotteryDraw).all()
    assert len(draws) == 2

def test_import_service_invalid_rows_rejected(db_session: Session, tmp_path):
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["draw_date", "first_prize", "last_two"])
        writer.writerow(["2023-11-01", "123", "78"]) # invalid first_prize (too short)
        writer.writerow(["invalid-date", "123456", "90"]) # invalid date
        writer.writerow(["2023-11-16", "654321", "9"]) # invalid last_two
        
    importer = CSVImporter()
    service = ImportService(db_session, importer)
    results = service.process_import(str(csv_file))
    
    assert results["total_rows"] == 3
    assert results["imported"] == 0
    assert results["rejected_invalid"] == 3
    assert len(results["errors"]) == 3

class ExplodingImporter(CSVImporter):
    def parse(self, file_path):
        raise RuntimeError("Disk failed!")

def test_import_service_rollback_works(db_session: Session, tmp_path):
    importer = ExplodingImporter()
    service = ImportService(db_session, importer)
    
    with pytest.raises(RuntimeError, match="Disk failed!"):
        service.process_import("fake.csv")
        
    # Transaction rolled back, but log should be failed
    logs = db_session.query(ImportLog).all()
    assert len(logs) == 1
    assert logs[0].status == "failed"
    assert "Disk failed" in logs[0].error_message
