from typing import List, Dict, Any, Tuple

class DatasetSplitter:
    @staticmethod
    def split(dataset: List[Dict[str, Any]], train_ratio: float = 0.7, val_ratio: float = 0.15, test_ratio: float = 0.15) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Deterministically splits the dataset chronologically based on the provided ratios.
        Note: Because the dataset contains 100 rows per draw (all sharing the same draw_date), 
        we must ensure splits happen on draw boundaries to prevent data leakage (where some candidates 
        of a draw are in train and others in val/test).
        """
        if not dataset:
            return [], [], []
            
        # Group rows by draw_date to ensure boundaries
        draws_groups = []
        current_date = dataset[0].get("draw_date")
        current_group = []
        
        for row in dataset:
            if row.get("draw_date") != current_date:
                draws_groups.append(current_group)
                current_date = row.get("draw_date")
                current_group = [row]
            else:
                current_group.append(row)
                
        if current_group:
            draws_groups.append(current_group)
            
        total_draws = len(draws_groups)
        
        # Calculate indices
        train_end = int(total_draws * train_ratio)
        val_end = train_end + int(total_draws * val_ratio)
        
        # Split groups
        train_groups = draws_groups[:train_end]
        val_groups = draws_groups[train_end:val_end]
        test_groups = draws_groups[val_end:]
        
        # Flatten groups back to lists of rows
        train_set = [row for group in train_groups for row in group]
        val_set = [row for group in val_groups for row in group]
        test_set = [row for group in test_groups for row in group]
        
        return train_set, val_set, test_set
