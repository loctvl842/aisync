"""Database configuration."""

from sqlalchemy import util
from sqlalchemy import AsyncAdaptedQueuePool, Engine, NullPool, event, exc
from sqlalchemy.engine.interfaces import _CoreAnyExecuteParams
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm._typing import OrmExecuteOptionsParameter
from sqlalchemy.orm.session import _BindArguments
from sqlalchemy.sql import Select

import asyncio
import enum
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Optional, Set, Type, Union
from aisync.log import LogEngine
from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy.sql.base import Executable

from aisync_api.env import Settings, get_settings


logger = LogEngine("Database.config")

# Metrics
DB_POOL_SIZE = Gauge(
    "db_connection_pool_size",
    "Current database connection pool size",
    ["database", "pool_type"],
)
DB_OPERATION_DURATION = Histogram(
    "db_operation_duration_seconds",
    "Duration of database operations",
    ["operation_type", "database"],
)
DB_ERRORS = Counter(
    "db_errors_total",
    "Total number of database errors",
    ["error_type", "database"],
)


class DatabaseRole(str, enum.Enum):
    """Database roles for different types of operations."""

    WRITER = "writer"
    READER = "reader"
    ANALYTICS = "analytics"


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""

    uri: str
    min_pool_size: int = 5
    max_pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False
    retry_limit: int = 3
    retry_delay: float = 0.1


class DatabaseHealthCheck:
    """Health check functionality for database connections."""

    def __init__(self, engine: AsyncEngine, config: DatabaseConfig):
        self.engine = engine
        self.config = config
        self.last_check: float = 0
        self.check_interval: float = 60  # seconds

    async def is_healthy(self) -> bool:
        """Check if database connection is healthy."""
        current_time = time.time()
        if current_time - self.last_check < self.check_interval:
            return True

        try:
            async with self.engine.connect() as conn:
                await conn.execute(Select(1))
                self.last_check = current_time
                return True
        except Exception as e:
            DB_ERRORS.labels(error_type="health_check", database=self.config.uri).inc()
            logger.error(f"Database health check failed: {str(e)}")
            return False


class RetryingDatabaseSession(AsyncSession):
    """
    Enhanced AsyncSession with retry capabilities for transient failures.
    """

    def __init__(
        self,
        bind: Optional[Union[AsyncEngine, Engine]] = None,
        *,
        retry_limit: int = 3,
        retry_delay: float = 0.1,
        allowed_exceptions: Optional[Set[Type[Exception]]] = None,
        **kwargs: Any,
    ):
        """
        Initialize the retrying session.

        Args:
            *args: Arguments to pass to AsyncSession
            retry_limit: Maximum number of retry attempts
            retry_delay: Base delay between retries (will be exponentially increased)
            allowed_exceptions: Set of exceptions that trigger retries
            **kwargs: Keyword arguments to pass to AsyncSession
        """
        super().__init__(bind=bind, **kwargs)
        self.retry_limit = retry_limit
        self.retry_delay = retry_delay
        self.allowed_exceptions = allowed_exceptions or {
            exc.OperationalError,
            exc.InternalError,
            exc.DBAPIError,
            exc.TimeoutError,
        }

    async def _execute_with_retry(
        self,
        operation: Any,
        fn_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a database operation with retry logic."""
        last_error = None
        for attempt in range(self.retry_limit):
            try:
                with DB_OPERATION_DURATION.labels(
                    operation_type=fn_name,
                    database=str(self.bind.url if self.bind else "unknown"),
                ).time():
                    original_method = getattr(super(), fn_name)
                    return await original_method(operation, *args, **kwargs)
            except Exception as e:
                if not any(isinstance(e, exc) for exc in self.allowed_exceptions):
                    raise
                if attempt == self.retry_limit - 1:
                    logger.error(f"Max retries reached for database operation: {str(e)}")
                    DB_ERRORS.labels(
                        error_type="retry_exhausted",
                        database=str(self.bind.url if self.bind else "unknown"),
                    ).inc()
                    raise last_error

                delay = self.retry_delay * (2**attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{self.retry_limit} failed for {fn_name}. "
                    f"Retrying in {delay:.2f}s. Error: {str(e)}"
                )
                await asyncio.sleep(delay)

    async def execute(
        self,
        statement: Executable,
        params: Optional[_CoreAnyExecuteParams] = None,
        *,
        execution_options: OrmExecuteOptionsParameter = util.EMPTY_DICT,
        bind_arguments: Optional[_BindArguments] = None,
        **kw: Any,
    ):
        return await self._execute_with_retry(
            statement,
            "execute",
            params=params,
            execution_options=execution_options,
            bind_arguments=bind_arguments,
            **kw,
        )


class DatabaseSessionManager:
    """Manages database sessions with advanced features."""

    def __init__(
        self,
        config: DatabaseConfig,
        settings: Settings = get_settings(),
        testing: bool = False,
    ):
        self.config = config
        self.settings = settings
        self.testing = testing
        self.engines: Dict[DatabaseRole, AsyncEngine] = {}
        self.health_checks: Dict[DatabaseRole, DatabaseHealthCheck] = {}
        self._initialize_engines()
        self._setup_session_factory()

    def _initialize_engines(self):
        """Initialize database engines for different roles."""
        engine_args = self._get_engine_args()

        for role in DatabaseRole:
            engine = create_async_engine(self.config.uri, **engine_args)
            self.engines[role] = engine
            self.health_checks[role] = DatabaseHealthCheck(engine, self.config)

            event.listen(engine.sync_engine, "connect", self._on_connect(role))
            event.listen(engine.sync_engine, "checkout", self._on_checkout(role))
            event.listen(engine.sync_engine, "checkin", self._on_checkin(role))
            event.listen(engine.sync_engine, "close", self._on_close(role))

    def _on_connect(self, role: DatabaseRole):
        def handler(dbapi_connection, connection_record):
            logger.info(f"New database connection established for {role}")
            current_size = DB_POOL_SIZE.labels(database=self.config.uri, pool_type=role.value)._value.get() or 0
            DB_POOL_SIZE.labels(database=self.config.uri, pool_type=role.value).set(current_size + 1)

        return handler

    def _on_checkout(self, role: DatabaseRole):
        """'checkout' event: When a connection is borrowed from the pool"""

        def handler(dbapi_connection, connection_record, connection_proxy):
            logger.info(f"Database connection borrowed for {role}")

        return handler

    def _on_checkin(self, role: DatabaseRole):
        """'checkin' event: When a connection is returned to the pool"""

        def handler(dbapi_connection, connection_record):
            current_size = DB_POOL_SIZE.labels(database=self.config.uri, pool_type=role.value)._value.get() or 1
            DB_POOL_SIZE.labels(database=self.config.uri, pool_type=role.value).set(max(0, current_size - 1))

        return handler

    def _on_close(self, role: DatabaseRole):
        def handler(dbapi_connection, connection_record):
            logger.info(f"Database connection closed for {role}")
            current_size = DB_POOL_SIZE.labels(database=self.config.uri, pool_type=role.value)._value.get() or 1
            DB_POOL_SIZE.labels(database=self.config.uri, pool_type=role.value).set(max(0, current_size - 1))

        return handler

    def _setup_session_factory(self) -> None:
        """Set up the session factory."""
        self.session_factory = async_sessionmaker(
            class_=RetryingDatabaseSession,
            expire_on_commit=False,
            retry_limit=self.config.retry_limit,
            retry_delay=self.config.retry_delay,
        )

    @asynccontextmanager
    async def session(self, role: DatabaseRole = DatabaseRole.WRITER) -> AsyncGenerator[RetryingDatabaseSession, None]:
        """Get a database session with automatic cleanup."""
        session = self.session_factory(bind=self.engines[role])
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            DB_ERRORS.labels(error_type="session_error", database=self.config.uri).inc()
            await session.rollback()
            raise
        finally:
            await session.close()

    async def check_all_connections(self) -> Dict[DatabaseRole, bool]:
        """Check health of all database connections."""
        return {role: await health_check.is_healthy() for role, health_check in self.health_checks.items()}

    def _get_engine_args(self) -> Dict[str, Any]:
        """Get engine configuration arguments."""
        if self.testing:
            return {"poolclass": NullPool, "echo": self.config.echo}

        return {
            "poolclass": AsyncAdaptedQueuePool,
            "pool_size": self.config.max_pool_size,
            "max_overflow": self.config.max_overflow,
            "pool_timeout": self.config.pool_timeout,
            "pool_recycle": self.config.pool_recycle,
            "pool_pre_ping": True,
            "echo": self.config.echo,
        }


async def main():
    config = DatabaseConfig(
        uri="postgresql+asyncpg://postgres:thangcho@localhost:5432/test",
        retry_limit=3,
        retry_delay=0.1,
        min_pool_size=5,
        max_pool_size=20,
    )

    db_manager = DatabaseSessionManager(config)

    async with db_manager.session() as session:
        # Example query with retry
        query = Select(2)
        result = await session.execute(query)
        print("vaicalon", result.scalar())

    # Health check
    # health_status = await db_manager.check_all_connections()
    # print(f"Database health status: {health_status}")


if __name__ == "__main__":
    asyncio.run(main())
