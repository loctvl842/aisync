from __future__ import annotations

from sqlalchemy import UUID, ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase

import uuid
from enum import Enum
from typing import List


class Base(AsyncAttrs, DeclarativeBase):
    """Enhanced base class for SQLAlchemy models."""


"""
Auth
"""


class TblUser(Base):
    __tablename__ = "auth_user"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    email = mapped_column(String, unique=True, index=True)
    hashed_password = mapped_column(String)

    user_roles: Mapped[List[TblUserRole]] = relationship(
        "TblUserRole", back_populates="user", cascade="save-update, merge, delete, delete-orphan"
    )
    roles: Mapped[List[TblRole]] = relationship("TblRole", secondary="auth_user_role", viewonly=True)
    projects: Mapped[List[TblProject]] = relationship(
        "TblProject", back_populates="user", cascade="save-update, merge, delete"
    )


class Role(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"
    OWNER = "owner"
    SYSTEM = "system"


class TblRole(Base):
    __tablename__ = "auth_role"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name = mapped_column(String, unique=True, index=True)
    description = mapped_column(String)

    user_roles: Mapped[List[TblUserRole]] = relationship(
        "TblUserRole", back_populates="role", cascade="save-update, merge, delete, delete-orphan"
    )
    role_permissions: Mapped[List[TblRolePermission]] = relationship(
        "TblRolePermission", back_populates="role", cascade="save-update, merge, delete, delete-orphan"
    )
    users: Mapped[List[TblUser]] = relationship("TblUser", secondary="auth_user_role", viewonly=True)
    permissions: Mapped[List[TblPermission]] = relationship(
        "TblPermission", secondary="auth_role_permission", viewonly=True
    )


class TblUserRole(Base):
    __tablename__ = "auth_user_role"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = mapped_column(UUID, ForeignKey("auth_user.id", name="fk_user_role_user"))
    role_id = mapped_column(UUID, ForeignKey("auth_role.id", name="fk_user_role_role"))
    team_id = mapped_column(UUID, ForeignKey("proj_team.id", name="fk_user_role_team"))

    user: Mapped[TblUser] = relationship("TblUser", back_populates="user_roles")
    role: Mapped[TblRole] = relationship("TblRole", back_populates="user_roles")
    team: Mapped[TblTeam] = relationship("TblTeam", back_populates="user_roles")

    __table_args__ = (UniqueConstraint("user_id", "team_id", name="uq_user_team"),)


class TblPermission(Base):
    __tablename__ = "auth_permission"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name = mapped_column(String, unique=True, index=True)
    action = mapped_column(String, nullable=False, index=True)
    resource = mapped_column(String, nullable=False, index=True)
    description = mapped_column(String)

    role_permissions: Mapped[List[TblRolePermission]] = relationship(
        "TblRolePermission", back_populates="permission", cascade="save-update, merge, delete, delete-orphan"
    )
    roles: Mapped[List[TblRole]] = relationship("TblRole", secondary="auth_role_permission", viewonly=True)


class TblRolePermission(Base):
    __tablename__ = "auth_role_permission"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    role_id = mapped_column(UUID, ForeignKey("auth_role.id", name="fk_role_permission_role"))
    permission_id = mapped_column(UUID, ForeignKey("auth_permission.id", name="fk_role_permission_permission"))

    role: Mapped[TblRole] = relationship("TblRole", back_populates="role_permissions")
    permission: Mapped[TblPermission] = relationship("TblPermission", back_populates="role_permissions")


"""
Projects
"""


class TblTeam(Base):
    __tablename__ = "proj_team"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    description = mapped_column(String)

    projects: Mapped[List[TblProject]] = relationship(
        "TblProject", back_populates="team", cascade="save-update, merge, delete"
    )
    user_roles: Mapped[List[TblUserRole]] = relationship(
        "TblUserRole", back_populates="team", cascade="save-update, merge, delete"
    )


class TblProject(Base):
    __tablename__ = "proj_project"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    user_id = mapped_column(UUID, ForeignKey("auth_user.id", name="fk_project_user"))
    team_id = mapped_column(UUID, ForeignKey("proj_team.id", name="fk_project_team"))

    team: Mapped["TblTeam"] = relationship("TblTeam", back_populates="projects")
    user: Mapped["TblUser"] = relationship("TblUser", back_populates="projects")
