# backend/app/schemas/user.py

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChangePassword(BaseModel):
    old_password: str = Field(min_length=1, max_length=100)
    new_password: str = Field(min_length=6, max_length=100)


class UserStats(BaseModel):
    total_submissions: int
    accepted_submissions: int
    solved_problems: int
    acceptance_rate: float
    language_distribution: dict

class AdminUserItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class UserRoleUpdate(BaseModel):
    role: str = Field(pattern="^(admin|user)$")


class UserStatusUpdate(BaseModel):
    is_active: bool


class AdminStats(BaseModel):
    total_users: int
    total_admins: int
    active_users: int
    banned_users: int
    total_submissions: int
    total_accepted: int
    total_problems: int