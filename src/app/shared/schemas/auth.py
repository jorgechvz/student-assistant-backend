"""Authentication Schemas"""

from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):  # pylint: disable=missing-class-docstring
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)


class LoginRequest(BaseModel):  # pylint: disable=missing-class-docstring
    email: EmailStr
    password: str


class TokenResponse(BaseModel):  # pylint: disable=missing-class-docstring
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):  # pylint: disable=missing-class-docstring
    id: str
    email: str
    full_name: str
    is_active: bool


class LoginResponse(BaseModel):  # pylint: disable=missing-class-docstring
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
