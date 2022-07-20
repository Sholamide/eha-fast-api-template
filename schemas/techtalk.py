from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.sql import func


class TechTalkIn(BaseModel):
    title: str
    description: str
    thumbsup: int
    completed: bool = False
    timeoftalk: Optional[datetime]

    class Config:
        orm_mode = True


class TechTalk(BaseModel):
    id:  int
    title: str
    description: str
    thumbsup: int
    timeoftalk: Optional[datetime]
    completed: bool = False

    class Config:
        orm_mode = True
