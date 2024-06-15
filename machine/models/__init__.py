from core.db import Base  # noqa: F401, This import is necessary for Alembic to detect the models

from .user import User  # noqa: F401
from .chat_input import ChatInput  # noqa: F401
from .chat_output import ChatOutput  # noqa: F401
