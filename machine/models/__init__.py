from core.db import Base  # noqa: F401, This import is necessary for Alembic to detect the models

from .user import User  # noqa: F401
from .query_logs import QueryLogs  # noqa: F401
from .response_logs import ResponseLogs  # noqa: F401
