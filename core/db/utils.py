from functools import wraps
from uuid import uuid4

from core.db import sessions

from .session import Dialect


class SessionContext:
    def __init__(self, dialect: Dialect):
        self.dialect = dialect

    def __call__(self, fn):
        @wraps(fn)
        async def _session_context(*args, **kwargs):
            session_id = str(uuid4())
            context = sessions[self.dialect].set_session_context(session_id=session_id)
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                await sessions[self.dialect].session.remove()
                sessions[self.dialect].reset_session_context(context=context)

        return _session_context
