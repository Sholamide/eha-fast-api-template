from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserIn(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False

    class Config:
        orm_mode = True


class User(BaseModel):
    id: int
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False

    class Config:
        orm_mode = True


class UserInDB(User):
    hashed_password: str
