import enum


class Channel(str, enum.Enum):
    FILE_CHANGED = "file_changes"
    NODE_EXECUTION = "node_execution"
