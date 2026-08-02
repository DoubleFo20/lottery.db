import re
import unicodedata

class StringCleaner:
    @staticmethod
    def clean(value: any) -> str | None:
        """
        Applies basic string cleaning:
        - normalize unicode
        - trim whitespace
        - collapse spaces
        - null conversion
        """
        if value is None:
            return None
            
        value_str = str(value)
        
        # Normalize unicode
        value_str = unicodedata.normalize('NFKC', value_str)
        
        # Remove zero-width spaces and other invisible characters
        value_str = value_str.replace('\u200b', '')
        
        # Trim whitespace
        value_str = value_str.strip()
        
        # Collapse multiple spaces
        value_str = re.sub(r'\s+', ' ', value_str)
        
        # Normalize nulls
        if not value_str or value_str in ("-", "N/A", "null", "None"):
            return None
            
        return value_str
