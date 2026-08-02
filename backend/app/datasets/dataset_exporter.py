import csv
import json
import os
from datetime import datetime
from typing import List, Dict, Any

class DatasetExporter:
    @staticmethod
    def export_csv(dataset: List[Dict[str, Any]], filepath: str):
        if not dataset:
            return
            
        keys = dataset[0].keys()
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(dataset)

    @staticmethod
    def export_json(dataset: List[Dict[str, Any]], filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2)

    @staticmethod
    def export_parquet(dataset: List[Dict[str, Any]], filepath: str):
        try:
            import pandas as pd
            import pyarrow # ensures it's available
            
            if not dataset:
                return
                
            df = pd.DataFrame(dataset)
            df.to_parquet(filepath, index=False)
            
        except ImportError:
            # Gracefully skip if optional dependencies are not installed
            print("Parquet export skipped: pandas or pyarrow not installed.")

    @staticmethod
    def generate_metadata(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not dataset:
            return {}
            
        first_row = dataset[0]
        # Calculate missing values across the dataset
        missing_counts = {k: 0 for k in first_row.keys()}
        for row in dataset:
            for k, v in row.items():
                if v is None:
                    missing_counts[k] += 1
                    
        return {
            "total_samples": len(dataset),
            "feature_count": len(first_row) - 3, # minus draw_date, candidate, label
            "target_columns": ["label"],
            "missing_values": missing_counts,
            "generated_timestamp": datetime.now().isoformat()
        }
