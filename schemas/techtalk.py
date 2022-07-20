from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.sql import func


class TechTalkBase(BaseModel):
    id:  int
    title: str
    description: str
    thumbsup: int
    timeoftalk: Optional[datetime]
    completed: bool = False

    class Config:
        orm_mode = True


class TechTalkCreate(TechTalkBase):
    title: str


class TechTalkUpdate(TechTalkBase):
    pass


class TechTalkInDBBase(TechTalkBase):
    id:  int
    title: str
    # owner_id: int

    class Config:
        orm_mode = True


class TechTalk(TechTalkInDBBase):
    pass


class TechTalkInDB(TechTalkInDBBase):
    pass
