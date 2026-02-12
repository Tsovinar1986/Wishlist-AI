"""User schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None


class UserInDB(UserBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class UserResponse(UserInDB):
    """Public user info (no password)."""

    pass
