from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from typing import Annotated

from aisync_api.database.config import DatabaseRole
from aisync_api.dependencies import get_db_session

router = APIRouter(tags=["health"])


@router.get("/ping")
async def ping(session: Annotated[AsyncSession, Depends(get_db_session(DatabaseRole.READER))]):
    return {"ping": "pong!"}
