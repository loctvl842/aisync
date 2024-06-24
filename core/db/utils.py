from functools import wraps
from uuid import uuid4

from .session import Dialect, reset_session_context, session, set_session_context


class SessionContext:
    def __call__(self, fn, dialect: Dialect):
        @wraps(fn)
        async def _session_context(*args, **kwargs):
            session_id = str(uuid4())
            context = set_session_context(session_id=session_id)
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                await session.remove()
                reset_session_context(context=context)

        return _session_context
