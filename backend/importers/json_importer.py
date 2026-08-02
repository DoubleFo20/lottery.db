import json
from typing import List, Dict, Any
from .base_importer import BaseImporter

class JSONImporter(BaseImporter):
    @property
    def source_name(self) -> str:
        return "json"

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON file must contain a list of objects")
            
            # Clean values
            results = []
            for row in data:
                cleaned_row = {k.strip(): (str(v).strip() if v is not None and str(v).strip() else None) for k, v in row.items()}
                results.append(cleaned_row)
            return results
