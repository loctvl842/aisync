from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from functools import partial
from typing import Annotated, Optional

from aisync_api.database.config import DatabaseRole
from aisync_api.dependencies import get_db_session
from aisync_api.server.exceptions import BadRequestException
from .controller import AuthController
from .service import SystemAuth

AUTH_SERVICES = {
    "system": partial(SystemAuth),
}
SUPPORTED_PROVIDERS = list(AUTH_SERVICES.keys())


async def get_auth_provider(x_provider: Optional[str] = Header("system", alias="X-Auth-Provider")) -> str:
    provider = x_provider.lower()
    if provider and provider not in SUPPORTED_PROVIDERS:
        raise BadRequestException(
            f"Unsupported authentication provider: {provider}. "
            f"Supported providers are: {', '.join(SUPPORTED_PROVIDERS)}."
        )
    else:
        provider = provider or "system"
    return provider


def get_auth_service(provider: str):
    suppored_providers = AUTH_SERVICES.keys()
    if provider not in suppored_providers:
        raise BadRequestException(
            f"Unsupported authentication provider: {provider}. Supported providers are: {', '.join(suppored_providers)}."
        )
    make_auth_service = AUTH_SERVICES.get(provider)
    return make_auth_service()


async def get_auth_controller(auth_provider=Depends(get_auth_provider)) -> AuthController:
    return AuthController(auth_service=get_auth_service(auth_provider))


security = HTTPBearer()


async def authenticate(
    request: Request,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_provider: Annotated[str, Depends(get_auth_provider)],
    session: Annotated[AsyncSession, Depends(get_db_session(DatabaseRole.READER))],
):
    """Authenticate a user using the provided token and authentication provider.

    This function ensures that a user is authenticated based on the token and the authentication provider specified
    in the `X-Auth-Provider` header (default is `system`). If the user is already stored in `request.state.user`, it returns the cached
    user to avoid redundant authentication calls.

    Once authenticated, the user is cached in `request.state.user` for reuse within the same request lifecycle.

    **Usage and Impact on Database Session:**

    - **If used after the database session dependency:**

      ```python
      @router.post("/")
      async def create_project(
          body: CreateProjectRequest,
          session: Annotated[AsyncSession, Depends(get_db_session())],
          user: Annotated[Any, Depends(authenticate)],
      ):
      ```
      - In this case, the session is initialized **before** authentication, allowing it to be created with `DatabaseRole.WRITER`,
        enabling **write operations**.

    - **If used before the database session dependency:**

      ```python
      @router.post("/")
      async def create_project(
          user: Annotated[Any, Depends(authenticate)],
          session: Annotated[AsyncSession, Depends(get_db_session())],
      ):
      ```
      - Since `authenticate` initializes the session **first** with `DatabaseRole.READER`, the session remains in a
        **read-only transaction**. Any subsequent database operations in the request handler will be limited to read operations.

    **Notes:**
    - Ensure that `authenticate` is placed **after** `session` in the function signature if a writable transaction is required.
    - If `authenticate` is placed **before** `session`, the session will be **read-only** due to dependency injection order.
    - The authentication provider must be one of the `SUPPORTED_PROVIDERS`, otherwise, a `BadRequestException` will be raised.
    """
    if hasattr(request.state, "user"):
        return request.state.user
    auth_controller = AuthController(auth_service=get_auth_service(provider=auth_provider))
    user = await auth_controller.authenticate(session, access_token=token.credentials)
    request.state.user = user
    return user
