import csv
from typing import List, Dict, Any
from .base_importer import BaseImporter

class CSVImporter(BaseImporter):
    @property
    def source_name(self) -> str:
        return "csv"

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        results = []
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Strip spaces from keys and values
                cleaned_row = {k.strip(): (v.strip() if v and v.strip() else None) for k, v in row.items()}
                results.append(cleaned_row)
        return results
