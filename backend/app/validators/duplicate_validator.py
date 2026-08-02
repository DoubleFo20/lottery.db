from sqlalchemy.orm import Session
from app.repositories.lottery_draw import lottery_draw
from datetime import datetime

class DuplicateValidator:
    def __init__(self, db: Session):
        self.db = db

    def validate(self, draw_date: str) -> str | None:
        """
        Validates whether a draw for the given date already exists.
        Returns an error string if a duplicate is found, else None.
        """
        if not draw_date:
            return None # Date parsing handled by DateValidator
            
        try:
            # We assume draw_date is YYYY-MM-DD since DateValidator handles format
            parsed_date = datetime.strptime(str(draw_date), "%Y-%m-%d").date()
        except ValueError:
            return None # If it can't be parsed, let DateValidator catch it, not our job here
            
        existing_draw = lottery_draw.get_by_draw_date(self.db, draw_date=parsed_date)
        if existing_draw:
            return f"Duplicate draw found for date {draw_date}"
            
        return None
