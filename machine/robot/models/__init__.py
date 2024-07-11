from core.db import Base  # noqa: F401, This import is necessary for Alembic to detect the models

from .doc_collection import DocCollection  # noqa: F401
from .query_logs import QueryLogs  # noqa: F401
from .response_logs import ResponseLogs  # noqa: F401
from .tool_collection import ToolCollection  # noqa: F401
