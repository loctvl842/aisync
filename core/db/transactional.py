from functools import wraps

from core.db import Dialect

from .session import sessions


class Transactional:
    def __init__(self, dialect: Dialect = Dialect.PGVECTOR):
        self.dialect = dialect

    def __call__(self, fn):
        @wraps(fn)
        async def _transactional(*args, **kwargs):
            session = sessions[Dialect.PGVECTOR].session
            try:
                result = await fn(*args, **kwargs)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

            return result

        return _transactional
