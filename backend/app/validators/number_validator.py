class NumberValidator:
    @staticmethod
    def validate(field_name: str, value: any, required_length: int, is_required: bool = False) -> str | None:
        """
        Validates that a numeric field is purely digits and of the exact length.
        """
        if not value:
            if is_required:
                return f"{field_name} is required"
            return None
            
        value_str = str(value)
        if not value_str.isdigit():
            return f"{field_name} must be numeric"
            
        if len(value_str) != required_length:
            return f"{field_name} must be exactly {required_length} digits"
            
        return None
