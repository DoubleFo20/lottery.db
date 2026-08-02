class NumberCleaner:
    # Thai to Arabic digits mapping
    THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")

    @staticmethod
    def clean(value: any) -> str | None:
        """
        Cleans numeric strings:
        - Convert Thai digits to Arabic
        - Remove commas
        """
        if value is None:
            return None
            
        value_str = str(value)
        
        # Convert Thai digits
        value_str = value_str.translate(NumberCleaner.THAI_DIGITS)
        
        # Remove commas
        value_str = value_str.replace(",", "")
        
        if not value_str:
            return None
            
        return value_str
