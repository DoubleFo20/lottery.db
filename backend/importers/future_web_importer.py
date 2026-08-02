from typing import List, Dict, Any
from .base_importer import BaseImporter

class WebImporter(BaseImporter):
    """
    Interface placeholder for future government web scraper or API importer.
    Do not implement scraping logic yet as per Sprint 2.2 requirements.
    """
    
    @property
    def source_name(self) -> str:
        return "web_scraper"

    def parse(self, file_path: str = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("Web scraping logic will be implemented in future sprints.")
