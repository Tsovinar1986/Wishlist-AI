"""User schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


# Bcrypt (used for password hashing) accepts at most 72 bytes
PASSWORD_MAX_BYTES = 72


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v.encode("utf-8")) > PASSWORD_MAX_BYTES:
            raise ValueError("Password cannot be longer than 72 characters")
        return v


class UserUpdate(BaseModel):
    name: str | None = None
    pushover_user_key: str | None = None


class UserInDB(UserBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class UserResponse(UserInDB):
    """Public user info (no password)."""

    pass
