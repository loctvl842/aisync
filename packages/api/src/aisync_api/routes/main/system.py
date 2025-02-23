from fastapi import APIRouter, Depends

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Annotated, Optional
from pydantic import BaseModel

from aisync_api.database.models import TblRole
from aisync_api.dependencies import get_db_session


router = APIRouter(prefix="/system")


"""Create new Role
- API: 'POST /admin/roles/new'
- Body
```json
{
  "name": "string",
  "description": "string"
}
"""


class CreateRoleRequest(BaseModel):
    name: str
    description: Optional[str] = None


@router.post("/roles/new")
async def create_role(
    body: CreateRoleRequest,
    session: Annotated[AsyncSession, Depends(get_db_session())],
):
    stmt = insert(TblRole).values(name=body.name, description=body.description).returning(TblRole)
    result = await session.execute(stmt)
    role = result.scalars().first()
    await session.commit()
    return role
