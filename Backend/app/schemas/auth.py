"""Auth schemas (JWT, login, OAuth-ready)."""

from pydantic import BaseModel, EmailStr, field_validator

# Bcrypt accepts at most 72 bytes
_PASSWORD_MAX_BYTES = 72


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    type: str
    exp: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v.encode("utf-8")) > _PASSWORD_MAX_BYTES:
            raise ValueError("Password cannot be longer than 72 characters")
        return v


class RefreshRequest(BaseModel):
    refresh_token: str
