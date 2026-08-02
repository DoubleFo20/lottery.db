from datetime import datetime

class DateCleaner:
    @staticmethod
    def clean(value: any) -> str | None:
        """
        Normalizes dates to YYYY-MM-DD.
        Handles DD/MM/YYYY, DD-MM-YYYY, YYYY/MM/DD formats.
        """
        if not value:
            return None
            
        value_str = str(value).strip()
        
        # Define formats to try
        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%Y-%m-%d" # already correct format
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(value_str, fmt)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
                
        # If all fail, return the original string so the Validator can catch it
        return value_str
