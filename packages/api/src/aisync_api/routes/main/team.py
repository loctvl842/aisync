from fastapi import APIRouter, Depends

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Annotated, Optional
from uuid import UUID
from pydantic import BaseModel

from aisync_api.auth import authenticate
from aisync_api.database.models import Role, TblRole, TblTeam, TblUser, TblUserRole
from aisync_api.dependencies import get_db_session
from aisync_api.server.exceptions import SystemException
from aisync_api.types import Ok

router = APIRouter(prefix="/teams")


"""Create new Team
- API: 'POST /teams/new'
- Body
```json
{
  "name": "string",
  "description": "string"
}
"""


class CreateTeamRequest(BaseModel):
    name: str
    description: str


class CreateTeamResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None


async def get_role(session: AsyncSession, *, role: Role):
    result = await session.execute(select(TblRole).where(TblRole.name == role.value))
    r = result.scalars().first()
    return r


@router.post("/new", response_model=Ok[CreateTeamResponse])
async def create_team(
    body: CreateTeamRequest,
    session: Annotated[AsyncSession, Depends(get_db_session())],
    user: Annotated[TblUser, Depends(authenticate)],
):
    stmt = insert(TblTeam).values(name=body.name, description=body.description).returning(TblTeam)
    result = await session.execute(stmt)
    team = result.scalars().first()
    if not team:
        raise SystemException("Team creation failed. 1")
    owner_role = await get_role(session, role=Role.MEMBER)
    if owner_role is None:
        raise SystemException("Team creation failed. 2")
    stmt = insert(TblUserRole).values(user_id=user.id, role_id=owner_role.id, team_id=team.id).returning(TblUserRole)
    result = await session.execute(stmt)
    user_role = result.scalars().first()
    if not user_role:
        raise SystemException("Team creation failed. 3")
    await session.commit()
    return Ok(data={"id": team.id, "name": team.name, "description": team.description})


"""List Team Members
- API: 'GET /teams/{team_id}/members'
- Required fields: team_id
"""


@router.get("/{team_id}/members")
async def get_team_members(
    team_id: UUID,
    user: Annotated[TblUser, Depends(authenticate)],
    session: Annotated[AsyncSession, Depends(get_db_session())],
):
    stmt = (
        select(TblUser, TblRole.name.label("role"))
        .join(TblUserRole, TblUserRole.user_id == TblUser.id)
        .join(TblRole, TblRole.id == TblUserRole.role_id)
        .where(TblUserRole.team_id == team_id)
    )
    result = await session.execute(stmt)
    users = [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": role,
        }
        for user, role in result.all()
    ]
    return Ok(data=users)
