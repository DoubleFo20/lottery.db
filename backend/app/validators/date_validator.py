import re
from datetime import datetime

class DateValidator:
    @staticmethod
    def validate(draw_date: str) -> str | None:
        """
        Validates draw_date.
        Returns an error string if invalid, or None if valid.
        """
        if not draw_date:
            return "draw_date is missing"
            
        if not isinstance(draw_date, str):
            draw_date = str(draw_date)
            
        # Match YYYY-MM-DD
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", draw_date):
            return "draw_date must be in YYYY-MM-DD format"
            
        try:
            parsed_date = datetime.strptime(draw_date, "%Y-%m-%d")
        except ValueError:
            return "draw_date is not a valid calendar date"
            
        # Check invalid year
        current_year = datetime.now().year
        if parsed_date.year < 1900 or parsed_date.year > current_year + 5:
            return f"draw_date year {parsed_date.year} is out of realistic bounds"
            
        return None
