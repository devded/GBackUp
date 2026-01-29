from abc import ABC, abstractmethod
from typing import List, Dict, Any


class SourceProvider(ABC):
    @abstractmethod
    def get_repositories(self) -> List[Dict[str, Any]]:
        """Fetch list of repositories."""
        pass

    @abstractmethod
    def clone_repository(self, repo_info: Dict[str, Any], destination: str):
        """Clone a specific repository."""
        pass


class StorageProvider(ABC):
    @abstractmethod
    def upload(self, file_path: str, object_key: str, callback: Any = None):
        """Upload a file to storage."""
        pass


class Archiver(ABC):
    @abstractmethod
    def compress(self, source_dir: str, output_path: str):
        """Compress a directory."""
        pass
