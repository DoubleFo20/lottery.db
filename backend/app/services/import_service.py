from sqlalchemy.orm import Session
from datetime import datetime
from app.repositories.lottery_draw import lottery_draw
from app.repositories.import_log import import_log
from app.schemas.lottery_draw import LotteryDrawCreate
from app.schemas.import_log import ImportLogCreate
from app.schemas.import_schema import ImportRow
from pydantic import ValidationError
from importers.base_importer import BaseImporter

class ImportService:
    def __init__(self, db: Session, importer: BaseImporter):
        self.db = db
        self.importer = importer

    def process_import(self, file_path: str) -> dict:
        # Create an initial log entry
        log_data = ImportLogCreate(
            source=self.importer.source_name,
            import_date=datetime.now(),
            status="processing"
        )
        log_entry = import_log.create(db=self.db, obj_in=log_data)
        log_entry_id = log_entry.id
        self.db.commit() # Commit the 'processing' log first
        
        results = {
            "total_rows": 0,
            "imported": 0,
            "skipped_duplicates": 0,
            "rejected_invalid": 0,
            "errors": []
        }

        try:
            # Parse the file using the specific importer
            raw_data = self.importer.parse(file_path)
            results["total_rows"] = len(raw_data)
            
            from app.validators.row_validator import RowValidator
            from app.cleaners.row_cleaner import RowCleaner
            row_validator = RowValidator(self.db)
            
            for index, row in enumerate(raw_data):
                # Clean the row
                clean_row = RowCleaner.clean(row)
                
                # Validate the row using the validation engine
                validation_errors = row_validator.validate(clean_row)
                
                if validation_errors:
                    results["rejected_invalid"] += 1
                    # Aggregate errors for this row
                    error_str = " | ".join(validation_errors)
                    # If it's just a duplicate error, we can categorize it specifically
                    if len(validation_errors) == 1 and "Duplicate draw found" in validation_errors[0]:
                        results["skipped_duplicates"] += 1
                        results["rejected_invalid"] -= 1 # adjust since we counted it above
                        # We might still want to log it or skip it quietly based on previous behavior
                    else:
                        results["errors"].append(f"Row {index+1}: {error_str}")
                    continue
                
                # Parse to schema
                try:
                    valid_row = ImportRow(**clean_row)
                except ValidationError as e:
                    results["rejected_invalid"] += 1
                    results["errors"].append(f"Row {index+1}: Schema parse error - {e}")
                    continue
                
                # Insert the new draw
                draw_in = LotteryDrawCreate(
                    draw_date=valid_row.draw_date,
                    government_round=valid_row.government_round,
                    first_prize=valid_row.first_prize,
                    last_two=valid_row.last_two,
                    front_three=valid_row.front_three,
                    back_three=valid_row.back_three,
                    source=self.importer.source_name
                )
                lottery_draw.create(db=self.db, obj_in=draw_in)
                results["imported"] += 1
                
            # Final commit for all the valid draws
            self.db.commit()
            
            # Update log as completed
            log_entry = import_log.get(self.db, id=log_entry_id)
            if log_entry:
                log_entry.status = "completed"
                log_entry.rows_imported = results["imported"]
                self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            # Update log as failed
            log_entry = import_log.get(self.db, id=log_entry_id)
            if log_entry:
                log_entry.status = "failed"
                log_entry.error_message = str(e)[:500]
                self.db.commit()
            raise e
            
        return results
