from typing import Set

from aisync_api.services.watcher.handlers.base import FileChange, FileChangeHandler


class ExtensionBasedHandler(FileChangeHandler):
    """Handler that processes file changes based on their extension."""

    def __init__(self, extensions: Set[str]) -> None:
        self.extensions = {
            ext.lower() if ext.startswith(".") else f".{ext}" for ext in extensions
        }

    def can_handle(self, change: FileChange) -> bool:
        return change.extension in self.extensions
