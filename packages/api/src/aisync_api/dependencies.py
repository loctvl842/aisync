from fastapi import Request

from sqlalchemy.ext.asyncio import AsyncSession

import multiprocessing
from typing import AsyncGenerator

from .database.config import DatabaseConfig, DatabaseRole, DatabaseSessionManager
from .env import env

CPU_COUNT = multiprocessing.cpu_count()
DEFAULT_POOL_SIZE = min(20, CPU_COUNT * 2)
MAX_OVERFLOW = DEFAULT_POOL_SIZE // 2  # Adaptive overflow limit


_db_manager = None


def _init_db_manager():
    global _db_manager
    if _db_manager is None:
        config = DatabaseConfig(
            uri=env.SQLALCHEMY_DATABASE_URI,
            retry_limit=3,
            retry_delay=0.1,
            min_pool_size=max(5, DEFAULT_POOL_SIZE // 2),
            max_pool_size=DEFAULT_POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
        )
        _db_manager = DatabaseSessionManager(config)


_init_db_manager()


async def _db_session_dependency(
    request: Request, role: DatabaseRole = DatabaseRole.WRITER
) -> AsyncGenerator[AsyncSession, None]:
    if hasattr(request.state, "db_session"):
        yield request.state.db_session
        return

    await _db_manager.check_all_connections()
    async with _db_manager.session(role) as session:
        request.state.db_session = session
        yield session


def get_db_session(role: DatabaseRole = DatabaseRole.WRITER) -> AsyncSession:
    """
    Provides an asynchronous database session for FastAPI route handlers.

    This function serves as a FastAPI dependency, yielding an `AsyncSession`
    that is automatically managed (opened, yielded, and closed). It supports
    both read and write operations, ensuring efficient database access.

    Read vs. Write Transactions:
    ----------------------------
    - **Read Operations (`SELECT` queries)**:
        - Uses `DatabaseRole.READER` to ensure read-only transactions.
        - Begins a transaction with `SET TRANSACTION READ ONLY` to prevent accidental writes.
        - Rolls back the transaction upon completion to free resources.
        - Example usage in FastAPI:
          ```python
          from functools import partial

          @router.get("/items")
          async def get_items(
              db: AsyncSession = Depends(get_db_session(DatabaseRole.READER))
          ):
              result = await db.execute(text("SELECT * FROM items"))
              return result.fetchall()
          ```

    - **Write Operations (`INSERT`, `UPDATE`, `DELETE`)**:
        - Uses the default `DatabaseRole.WRITER` to allow modifications.
        - Transactions are automatically managed.
        - Example:
          ```python
          @router.post("/items")
          async def create_item(data: dict, db: AsyncSession = Depends(get_db_session())):
              async with db.begin():
                  await db.execute(text("INSERT INTO items (name) VALUES (:name)"), {"name": data["name"]})
              return {"message": "Item created"}
          ```
    """

    async def dependency(request: Request) -> AsyncGenerator[AsyncSession, None]:
        async for session in _db_session_dependency(request, role):
            yield session

    return dependency
