from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseImporter(ABC):
    """
    Abstract base class for all lottery data importers.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the data source."""
        pass

    @abstractmethod
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse the given file and return a list of dictionaries,
        each representing a single lottery draw.
        """
        pass
