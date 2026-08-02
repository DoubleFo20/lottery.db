from typing import Dict, Any

class DrawValidator:
    @staticmethod
    def validate(row: Dict[str, Any]) -> list[str]:
        """
        Validates missing required fields and invalid data types generally.
        Returns a list of errors (empty if valid).
        """
        errors = []
        
        # Missing required fields
        required_fields = ["draw_date", "first_prize"]
        for field in required_fields:
            val = row.get(field)
            if val is None or str(val).strip() == "":
                errors.append(f"Missing required field: {field}")
                
        # Basic data type sanity checks
        # government_round, if present, should be convertible to string
        if row.get("government_round") is not None:
            if not isinstance(row["government_round"], (str, int)):
                errors.append("government_round has an invalid data type")
                
        # Source could be required theoretically but it's set by importer
        
        return errors
