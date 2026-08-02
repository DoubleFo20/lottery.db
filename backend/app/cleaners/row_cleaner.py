from typing import Dict, Any
from app.cleaners.string_cleaner import StringCleaner
from app.cleaners.number_cleaner import NumberCleaner
from app.cleaners.date_cleaner import DateCleaner

class RowCleaner:
    @staticmethod
    def clean(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cleans an entire row dictionary.
        """
        cleaned = {}
        for key, value in row.items():
            # Apply base string cleaning to all fields
            val = StringCleaner.clean(value)
            
            # Apply number cleaning to prize fields
            if key in ["first_prize", "last_two", "front_three", "back_three"]:
                val = NumberCleaner.clean(val)
                
            # Apply date cleaning
            if key == "draw_date":
                val = DateCleaner.clean(val)
                
            cleaned[key] = val
            
        return cleaned
