import pytest
from datetime import datetime
from app.validators.date_validator import DateValidator
from app.validators.number_validator import NumberValidator
from app.validators.draw_validator import DrawValidator
from app.validators.row_validator import RowValidator
from app.validators.duplicate_validator import DuplicateValidator

def test_date_validator():
    assert DateValidator.validate(None) == "draw_date is missing"
    assert DateValidator.validate("10-10-2023") == "draw_date must be in YYYY-MM-DD format"
    assert DateValidator.validate("2023-15-10") == "draw_date is not a valid calendar date"
    assert DateValidator.validate("1800-01-01") == "draw_date year 1800 is out of realistic bounds"
    assert DateValidator.validate("2023-11-01") is None

def test_number_validator():
    assert NumberValidator.validate("first_prize", "123456", 6, True) is None
    assert NumberValidator.validate("first_prize", "123", 6, True) == "first_prize must be exactly 6 digits"
    assert NumberValidator.validate("first_prize", "abcdef", 6, True) == "first_prize must be numeric"
    assert NumberValidator.validate("last_two", None, 2, False) is None
    assert NumberValidator.validate("first_prize", None, 6, True) == "first_prize is required"

def test_draw_validator():
    row = {"draw_date": "2023-11-01", "first_prize": "123456"}
    assert DrawValidator.validate(row) == []
    
    row_missing = {"draw_date": "2023-11-01"}
    assert DrawValidator.validate(row_missing) == ["Missing required field: first_prize"]
    
    row_invalid_type = {"draw_date": "2023-11-01", "first_prize": "123456", "government_round": []}
    assert DrawValidator.validate(row_invalid_type) == ["government_round has an invalid data type"]

# Mock DB and duplicate validator
class MockDB:
    pass

class MockDuplicateValidator:
    def __init__(self, db):
        pass
    def validate(self, date):
        if date == "2023-11-01":
            return "Duplicate draw found for date 2023-11-01"
        return None

def test_row_validator(monkeypatch):
    monkeypatch.setattr("app.validators.row_validator.DuplicateValidator", MockDuplicateValidator)
    validator = RowValidator(MockDB())
    
    # Valid row
    valid_row = {"draw_date": "2023-11-16", "first_prize": "123456"}
    assert validator.validate(valid_row) == []
    
    # Duplicate row
    duplicate_row = {"draw_date": "2023-11-01", "first_prize": "123456"}
    assert validator.validate(duplicate_row) == ["Duplicate draw found for date 2023-11-01"]
    
    # Multiple errors
    invalid_row = {"draw_date": "invalid", "first_prize": "12"}
    errors = validator.validate(invalid_row)
    assert len(errors) == 2
    assert "draw_date must be in YYYY-MM-DD format" in errors
    assert "first_prize must be exactly 6 digits" in errors
