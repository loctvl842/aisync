from __future__ import annotations

import jwt

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from pydantic import BaseModel

from aisync_api.database.models import TblUser
from aisync_api.server.exceptions import NotImplementedException, UnauthorizedException


class AuthVisitor(ABC):
    @abstractmethod
    def visit_system_auth(self, system_auth: AuthService):
        raise NotImplementedException()


class AuthService(ABC):
    @abstractmethod
    def accept(self, visitor: AuthVisitor):
        raise NotImplementedException()

    @abstractmethod
    async def authenticate(self, *args, **kwargs) -> TblUser:
        raise NotImplementedException()

    @abstractmethod
    async def register(self, *args, **kwargs):
        raise NotImplementedException()

    @abstractmethod
    async def login(self, *args, **kwargs):
        raise NotImplementedException()

    def create_token(
        self,
        data: dict[str, Any],
        *,
        expiry: Optional[datetime] = None,
        key: str,
        algorithm: Optional[str] = "HS256",
    ) -> Token:
        to_encode = data.copy()
        if expiry is None:
            # Then, default to 30 minutes if no duration provided
            expiry = datetime.now(timezone.utc) + timedelta(minutes=30)
        to_encode.update({"exp": expiry})
        encoded_jwt = jwt.encode(to_encode, key=key, algorithm=algorithm)
        return Token(value=encoded_jwt, data=data, expiry=expiry, key=key, algorithm=algorithm)

    def decode_token(
        self,
        *,
        key: str,
        token: str,
        algorithms: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, key=key, algorithms=algorithms)
            return payload
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException(
                "The token has expired. Please log in again.",
                detail={"type": "expired_token"},
            )
        except jwt.InvalidSignatureError:
            raise UnauthorizedException(
                "The token's signature is invalid.",
                detail={"type": "invalid_signature"},
            )
        except jwt.DecodeError:
            raise UnauthorizedException(
                "The token could not be decoded. Ensure it is a valid JWT.",
                detail={"type": "invalid_token"},
            )
        except jwt.MissingRequiredClaimError as e:
            raise UnauthorizedException(
                f"Missing required claim: {e.claim}",
                detail={"type": "missing_claim"},
            )
        except jwt.InvalidTokenError:
            raise UnauthorizedException(
                "The token is invalid. Please provide a valid token.",
                detail={"type": "invalid_token"},
            )


class Token(BaseModel):
    value: str
    data: dict[str, Any]
    expiry: datetime
    key: str
    algorithm: str

    def __str__(self) -> str:
        return self.value
