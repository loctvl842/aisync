import abc
import asyncio
from pathlib import Path

from aisync_api.services.watcher.file_watcher import ChangeType


class FileChange:
    """Data class representing a file change event"""

    def __init__(self, change_type: ChangeType, file_path: Path):
        self.type = change_type
        self.path = Path(file_path)
        self.timestamp = asyncio.get_event_loop().time()

    @property
    def extension(self) -> str:
        """Get the file extension"""
        return self.path.suffix.lower()


class FileChangeHandler(abc.ABC):
    """A file change handler that can be used to handle file changes."""

    @abc.abstractmethod
    async def handle_change(self, change: FileChange) -> None:
        """Handle a file change event"""

    @abc.abstractmethod
    async def can_handle(self, change: FileChange) -> bool:
        """Check if the handler can handle a file change event"""
