from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(UserBase):
    id: UUID
    role: str
    created_at: datetime
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserAdminRead(UserRead):
    pass
