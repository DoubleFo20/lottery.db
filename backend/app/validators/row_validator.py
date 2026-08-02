from typing import Dict, Any
from sqlalchemy.orm import Session
from app.validators.date_validator import DateValidator
from app.validators.number_validator import NumberValidator
from app.validators.draw_validator import DrawValidator
from app.validators.duplicate_validator import DuplicateValidator

class RowValidator:
    def __init__(self, db: Session):
        self.db = db
        self.duplicate_validator = DuplicateValidator(db)
        self.date_validator = DateValidator()
        self.number_validator = NumberValidator()
        self.draw_validator = DrawValidator()

    def validate(self, row: Dict[str, Any]) -> list[str]:
        """
        Aggregates all validation errors for a given row.
        Returns a list of error strings. Empty list means the row is valid.
        """
        errors = []
        
        # 1. Missing fields and data types
        draw_errors = self.draw_validator.validate(row)
        errors.extend(draw_errors)
        
        # 2. Date validation
        date_err = self.date_validator.validate(row.get("draw_date"))
        if date_err:
            errors.append(date_err)
            
        # 3. Duplicate validation
        if not date_err and row.get("draw_date"):
            # Only check for duplicates if date is valid
            dup_err = self.duplicate_validator.validate(row.get("draw_date"))
            if dup_err:
                errors.append(dup_err)
                
        # 4. Number validation
        fp_err = self.number_validator.validate("first_prize", row.get("first_prize"), 6)
        if fp_err:
            errors.append(fp_err)
            
        lt_err = self.number_validator.validate("last_two", row.get("last_two"), 2)
        if lt_err:
            errors.append(lt_err)
            
        ft_err = self.number_validator.validate("front_three", row.get("front_three"), 3)
        if ft_err:
            errors.append(ft_err)
            
        bt_err = self.number_validator.validate("back_three", row.get("back_three"), 3)
        if bt_err:
            errors.append(bt_err)
            
        return errors
