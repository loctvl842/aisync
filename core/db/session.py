from contextvars import ContextVar, Token
from enum import Enum
from uuid import uuid4

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.sql.expression import Delete, Insert, Update

from core.settings import settings

session_context: ContextVar[str] = ContextVar("session_context")


def get_session_context() -> str:
    return session_context.get()


def set_session_context(session_id: str) -> Token:
    return session_context.set(session_id)


def reset_session_context(context: Token) -> None:
    session_context.reset(context)


class EngineType(Enum):
    WRITER = "writer"
    READER = "reader"


class RoutingSession(Session):
    def __init__(self, engines, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engines = engines
    def get_bind(self, mapper=None, clause=None, **kw):
        if self._flushing or isinstance(clause, (Update, Delete, Insert)):
            return self.engines[EngineType.WRITER].sync_engine
        else:
            return self.engines[EngineType.READER].sync_engine

class DBSession:
    def __init__(self, database_uri):
        self.session_context: ContextVar[str] = ContextVar(str(uuid4()))
        self.engines = {
            EngineType.WRITER: create_async_engine(database_uri, pool_recycle=3600),
            EngineType.READER: create_async_engine(database_uri, pool_recycle=3600),
        }
        self.async_session_factory = async_sessionmaker(
            class_=AsyncSession,
            sync_session_class=RoutingSession,
            expire_on_commit=False,
            engines=self.engines,
        )
        self.session = async_scoped_session(
            session_factory=self.async_session_factory,
            scopefunc=self.get_session_context,
        )

    def get_session_context(self) -> str:
        return self.session_context.get()

    def set_session_context(self, session_id: str) -> Token:
        return self.session_context.set(session_id)

    def reset_session_context(self, context):
        self.session_context.reset(context)

    async def get_session(self):
        """
        Get database session
        """
        try:
            yield self.session
        finally:
            await self.session.close()

"""
All database sessions
"""

class DBType(Enum):
    POSTGRES = "postgres"
    PGVECTOR = "pgvector"


sessions = {
    DBType.POSTGRES: DBSession(settings.SQLALCHEMY_POSTGRES_URI),
    DBType.PGVECTOR: DBSession(settings.SQLALCHEMY_PGVECTOR_URI),
}

# TODO: Remove this
set_session_context = sessions[DBType.POSTGRES].set_session_context
reset_session_context = sessions[DBType.POSTGRES].reset_session_context
get_session = sessions[DBType.POSTGRES].get_session
session = sessions[DBType.POSTGRES].session

class Base(DeclarativeBase): ...
