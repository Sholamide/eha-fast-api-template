from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False


class UserCreate(UserBase):
    email: EmailStr
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str
