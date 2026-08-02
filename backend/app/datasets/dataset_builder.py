from typing import List, Dict, Any
from app.models.lottery_draw import LotteryDraw
from app.features.feature_pipeline import FeaturePipeline

class DatasetBuilder:
    def __init__(self, draws: List[LotteryDraw]):
        """
        Initializes with a chronological list of historical draws (oldest first).
        """
        self.draws = draws

    def build_dataset(self, min_history: int = 10) -> List[Dict[str, Any]]:
        """
        Builds the supervised learning dataset.
        For each draw (after min_history), it generates 100 candidate rows (00-99).
        Target is 1 if candidate matches the actual 'last_two' of that draw, else 0.
        Returns a list of dictionaries (rows).
        """
        dataset = []
        
        # We need a list of strings for the history to pass to FeaturePipeline
        # specifically for the target property we want to predict (e.g. last_two).
        history_last_two = [d.last_two for d in self.draws if d.last_two]
        
        for i in range(min_history, len(self.draws)):
            current_draw = self.draws[i]
            if not current_draw.last_two:
                continue
                
            # History slice up to the current draw (exclusive)
            history_slice = history_last_two[:i]
            actual_winner = current_draw.last_two
            
            for candidate_int in range(100):
                candidate_str = f"{candidate_int:02d}"
                
                # Extract features for this candidate based on past history
                row_features = FeaturePipeline.build_features_for_string(candidate_str, history_slice)
                
                # Attach metadata (draw_date can be used for splitting or identifying rows)
                row_features["draw_date"] = current_draw.draw_date.strftime("%Y-%m-%d") if current_draw.draw_date else None
                row_features["candidate"] = candidate_str
                
                # Attach Target label
                row_features["label"] = 1 if candidate_str == actual_winner else 0
                
                dataset.append(row_features)
                
        return dataset
