import asyncio
import enum
from pathlib import Path
from typing import Callable, Literal, Optional, Set, TypedDict, Union

from aisync_api.server.log import LogEngine
from watchfiles import Change, awatch
from watchfiles.main import FileChange

AllExtensions = Literal["*"]


class ChangeType(enum.Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


class ChangeInfo(TypedDict):
    type: ChangeType
    path: str


class FileWatcher:
    """A service that monitors file changes"""

    def __init__(
        self,
        watch_path: Union[str, Path],
        callback: Optional[Callable] = None,
        file_extensions: Union[AllExtensions, Set[str]] = "*",
        recursive: bool = True,
    ):
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.recursive = recursive
        self.log = LogEngine(self.__class__.__name__)
        self.file_extensions = file_extensions
        self._stop_event = asyncio.Event()

        if not self.watch_path.exists():
            raise ValueError(f"Watch path does not exist: {self.watch_path}")

    async def start_watching(self) -> None:
        """Start watching the file system for changes"""
        self.log.info(f"Start watching path: {self.watch_path}")

        try:
            async for changes in awatch(
                self.watch_path,
                watch_filter=None,
                recursive=self.recursive,
                stop_event=self._stop_event,
            ):
                await self._handle_changes(changes)
        except Exception as e:
            self.log.error(f"Error in watching files: {e}")
            raise

    async def stop(self):
        """Gracefully stop the watcher"""
        self._stop_event.set()

    async def _handle_changes(self, changes: Set[FileChange]):
        """
        Process detected changes and trigger the callback function
        """
        for change_type, file_path in changes:
            self.log.info(f"Detected changes in '{file_path}'. Reloading...")
            if not self._should_process_file(file_path):
                continue
            change_types = {
                Change.added: ChangeType.ADDED,
                Change.modified: ChangeType.MODIFIED,
                Change.deleted: ChangeType.DELETED,
            }
            change_info: ChangeInfo = {
                "type": change_types[change_type],
                "path": str(file_path),
            }
            if self.callback:
                try:
                    await self.callback(change_info)
                except Exception as e:
                    self.log.error(f"Error in callback: {e}")

    def _should_process_file(self, file_path: str) -> bool:
        """Determine if a file should be processed"""

        if self.file_extensions == "*":
            return True
        return Path(file_path).suffix.lower() in self.file_extensions
