from fastapi import APIRouter, Depends

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Annotated
from pydantic import BaseModel

from aisync_api.auth import authenticate
from aisync_api.auth.permissions import Permission
from aisync_api.dependencies import get_db_session
from aisync_api.database.models import TblProject, TblUser

router = APIRouter(prefix="/projects")


class CreateProjectRequest(BaseModel):
    name: str


@router.post("/")
async def create_project(
    body: CreateProjectRequest,
    session: Annotated[AsyncSession, Depends(get_db_session())],
    user: Annotated[TblUser, Depends(authenticate)],
    # restrict_access: Annotated[bool, Depends(Permission())],
):
    stmt = insert(TblProject).values(name=body.name, user_id=user.id).returning(TblProject)
    result = await session.execute(stmt)
    project = result.scalars().first()
    await session.commit()
    return project
