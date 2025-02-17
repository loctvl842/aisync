import asyncio
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import insert
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import Select

from aisync_api.database.config import DatabaseConfig, DatabaseSessionManager
from aisync_api.database.models import User
from aisync_api.env import env

router = APIRouter(tags=["health"])


async def get_session():
    config = DatabaseConfig(
        uri=env.SQLALCHEMY_DATABASE_URI,
        retry_limit=3,
        retry_delay=0.1,
        min_pool_size=5,
        max_pool_size=20,
    )
    db_manager = DatabaseSessionManager(config)
    async with db_manager.session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/ping")
async def ping(session: SessionDep):
    query = Select(2)
    await asyncio.sleep(2)
    result = await session.execute(query)
    stmt = insert(User).values(
        email="test@test.com",
        hashed_password="test",
    )
    result = await session.execute(stmt)
    await session.commit()
    return {
        "ping": "pong!",
        "result": result,
    }
