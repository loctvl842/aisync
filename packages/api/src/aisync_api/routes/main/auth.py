from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from typing import Annotated
from pydantic import BaseModel

from aisync_api.auth import AuthController, get_auth_controller
from aisync_api.database.config import DatabaseRole
from aisync_api.dependencies import get_db_session
from aisync_api.types import Ok

router = APIRouter(prefix="/auth")

"""Sign Up

- API: 'POST /auth/signup'
- Required fields: email, password
- Body
```json
{
  "email": "string",
  "password": "string"
}
"""


class SignUpRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
async def signup(
    body: SignUpRequest,
    auth_controller: Annotated[AuthController, Depends(get_auth_controller)],
    session: Annotated[AsyncSession, Depends(get_db_session())],
):
    tokens = await auth_controller.register(session, body.email, body.password)
    return Ok(data=tokens)


"""Sign In

- API: 'POST /auth/signin'
- Required fields: email, password
- Body
```json
{
  "email": "string",
  "password": "string"
}
"""


class SignInRequest(BaseModel):
    email: str
    password: str


@router.post("/signin")
async def signin(
    body: SignInRequest,
    auth_controller: Annotated[AuthController, Depends(get_auth_controller)],
    session: Annotated[AsyncSession, Depends(get_db_session(DatabaseRole.READER))],
):
    tokens = await auth_controller.login(session, body.email, body.password)
    return Ok(data=tokens)
