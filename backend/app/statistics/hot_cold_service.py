from typing import List, Dict, Any, Tuple
from collections import Counter
from app.models.lottery_draw import LotteryDraw

class HotColdService:
    def __init__(self, draws: List[LotteryDraw]):
        # draws should be sorted chronologically (oldest first)
        self.draws = draws

    def analyze_last_two(self) -> Dict[str, Any]:
        """
        Analyzes hot/cold status, last seen, and missing streak for the 'last_two' prize.
        Returns a dictionary keyed by the number (00-99).
        """
        stats = {f"{i:02d}": {"count": 0, "last_seen": None, "missing_streak": 0, "current_streak": 0} for i in range(100)}
        
        total_draws = len(self.draws)
        
        for idx, draw in enumerate(self.draws):
            if draw.last_two and len(draw.last_two) == 2:
                num = draw.last_two
                if num in stats:
                    # Calculate missing gap
                    last_seen_idx = stats[num].get("last_seen_idx", -1)
                    gap = idx - last_seen_idx - 1
                    
                    if gap > stats[num]["missing_streak"]:
                        stats[num]["missing_streak"] = gap
                        
                    stats[num]["count"] += 1
                    stats[num]["last_seen_idx"] = idx
                    
        # Finalize stats
        for num, data in stats.items():
            last_idx = data.get("last_seen_idx", -1)
            if last_idx != -1:
                data["last_seen"] = total_draws - 1 - last_idx
                # Also check if current streak to the end is the longest missing streak
                current_gap = total_draws - 1 - last_idx
                if current_gap > data["missing_streak"]:
                    data["missing_streak"] = current_gap
            else:
                data["last_seen"] = total_draws # Never seen
                data["missing_streak"] = total_draws
                
            data.pop("last_seen_idx", None)
            
        return stats
        
    def get_hottest(self, n: int = 5) -> List[Tuple[str, int]]:
        stats = self.analyze_last_two()
        # Sort by count desc, then last_seen asc (more recently seen is hotter)
        sorted_stats = sorted(stats.items(), key=lambda item: (-item[1]["count"], item[1]["last_seen"]))
        return [(k, v["count"]) for k, v in sorted_stats[:n]]
        
    def get_coldest(self, n: int = 5) -> List[Tuple[str, int]]:
        stats = self.analyze_last_two()
        # Sort by count asc, then last_seen desc (longer unseen is colder)
        sorted_stats = sorted(stats.items(), key=lambda item: (item[1]["count"], -item[1]["last_seen"]))
        return [(k, v["count"]) for k, v in sorted_stats[:n]]
