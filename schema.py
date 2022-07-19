from pydantic import BaseModel, EmailStr
from typing import Optional


class TechTalkIn(BaseModel):
    title: str
    description: str
    thumbsup: int
    completed: bool = False

    class Config:
        orm_mode = True


class TechTalk(BaseModel):
    id:  int
    title: str
    description: str
    thumbsup: int
    completed: bool = False

    class Config:
        orm_mode = True


class UserIn(BaseModel):
    full_name: str
    email: EmailStr
    is_active: Optional[bool] = True
    is_superuser: bool = False

    class Config:
        orm_mode = True


class User(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    is_superuser: bool

    class Config:
        orm_mode = True
