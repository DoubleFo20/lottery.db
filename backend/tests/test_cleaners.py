import pytest
from app.cleaners.string_cleaner import StringCleaner
from app.cleaners.number_cleaner import NumberCleaner
from app.cleaners.date_cleaner import DateCleaner
from app.cleaners.row_cleaner import RowCleaner

def test_string_cleaner():
    # Trim spaces
    assert StringCleaner.clean("  hello  ") == "hello"
    
    # Collapse multiple spaces
    assert StringCleaner.clean("a    b") == "a b"
    
    # Unicode normalize
    assert StringCleaner.clean("hello\u200bworld") == "helloworld" # Zero-width space
    
    # Null conversion
    assert StringCleaner.clean("") is None
    assert StringCleaner.clean("-") is None
    assert StringCleaner.clean("N/A") is None
    assert StringCleaner.clean("null") is None
    assert StringCleaner.clean("None") is None
    assert StringCleaner.clean(None) is None

def test_number_cleaner():
    # Thai digits
    assert NumberCleaner.clean("๑๒๓๔๕๖") == "123456"
    assert NumberCleaner.clean("๐") == "0"
    
    # Comma removal
    assert NumberCleaner.clean("1,234,567") == "1234567"
    
    assert NumberCleaner.clean("") is None
    assert NumberCleaner.clean(None) is None

def test_date_cleaner():
    assert DateCleaner.clean("01/11/2023") == "2023-11-01"
    assert DateCleaner.clean("01-11-2023") == "2023-11-01"
    assert DateCleaner.clean("2023/11/01") == "2023-11-01"
    assert DateCleaner.clean("2023-11-01") == "2023-11-01"
    assert DateCleaner.clean("invalid") == "invalid"
    assert DateCleaner.clean(None) is None

def test_row_cleaner():
    raw_row = {
        "draw_date": " 01/11/2023 ",
        "government_round": "-",
        "first_prize": "๑๒๓,๔๕๖",
        "last_two": " ๙๐  ",
        "front_three": "null",
        "back_three": "1,2,3"
    }
    
    clean_row = RowCleaner.clean(raw_row)
    
    assert clean_row["draw_date"] == "2023-11-01"
    assert clean_row["government_round"] is None
    assert clean_row["first_prize"] == "123456"
    assert clean_row["last_two"] == "90"
    assert clean_row["front_three"] is None
    assert clean_row["back_three"] == "123"
