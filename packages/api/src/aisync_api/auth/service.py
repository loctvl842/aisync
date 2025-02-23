from itsdangerous import URLSafeSerializer

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timedelta, timezone
from typing import Optional

from aisync.log import LogEngine
from aisync_api.database.models import TblUser
from aisync_api.env import env
from aisync_api.server.exceptions import BadRequestException, UnauthorizedException
from .base import AuthService, AuthVisitor


class SystemAuth(AuthService):
    def __init__(self):
        self.logger = LogEngine(self.__class__.__name__)
        self.serializer = URLSafeSerializer(env.AUTH_PASSWORD_SECRET)

    async def accept(self, visitor: AuthVisitor):
        return await visitor.visit_system_auth(self)

    async def authenticate(self, session, *, access_token: str) -> TblUser:
        payload = self.decode_token(
            key=env.AUTH_ACCESS_TOKEN_SECRET,
            token=access_token,
            algorithms=["HS256"],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid access token.")
        stmt = select(TblUser).where(TblUser.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise UnauthorizedException("Invalid access token.")
        return user

    async def create_auth_tokens(self, user: TblUser, *, expiry: Optional[datetime] = None):
        access_token = self.create_token(
            {
                "sub": str(user.id),
                "email": user.email,
            },
            expiry=expiry or datetime.now(timezone.utc) + timedelta(days=env.AUTH_ACCESS_TOKEN_EXPIRY),
            key=env.AUTH_ACCESS_TOKEN_SECRET,
        )
        refresh_token = self.create_token(
            {"sub": str(user.id)},
            expiry=datetime.now(timezone.utc) + timedelta(days=env.AUTH_REFRESH_TOKEN_EXPIRY),
            key=env.AUTH_REFRESH_TOKEN_SECRET,
        )
        id_token = self.create_token(
            {
                "sub": str(user.id),
                "email": user.email,
            },
            expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            key=env.AUTH_ID_TOKEN_SECRET,
        )
        expires_in = int((access_token.expiry - datetime.now(timezone.utc)).total_seconds() * 1000)
        return {
            "token_type": "Bearer",
            "access_token": str(access_token),
            "refresh_token": str(refresh_token),
            "id_token": str(id_token),
            "expires_in": expires_in,
        }

    async def register(self, session: AsyncSession, email: str, password: str) -> TblUser:
        stmt = select(TblUser).where(TblUser.email == email)
        result = await session.execute(stmt)
        user = result.scalars().first()
        if user:
            raise BadRequestException("Email already exists.")

        hased_password = self._hash_password(password)
        user = TblUser(email=email, hashed_password=hased_password)
        session.add(user)

        await session.commit()
        tokens = await self.create_auth_tokens(user)

        return tokens

    async def login(self, session: AsyncSession, email: str, password: str) -> TblUser:
        stmt = select(TblUser).where(TblUser.email == email)
        result = await session.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise UnauthorizedException("Invalid email or password.")
        if not self.verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password.")
        tokens = await self.create_auth_tokens(user)
        self.logger.info(f"User {user.email} logged in.")
        return tokens

    def _hash_password(self, password: str) -> str:
        return self.serializer.dumps(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            stored_password = self.serializer.loads(hashed_password)
            return stored_password == plain_password
        except Exception as _:
            return False
