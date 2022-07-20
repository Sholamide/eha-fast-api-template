from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, DateTime, ForeignKey, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.baseclass import Base

if TYPE_CHECKING:
    from .user import User  # noqa: F401


class Talk(Base):
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String, index=True)
    thumbsup = Column(Integer)
    completed = Column(Boolean, default=False)
    timeOfTalk = Column(DateTime(timezone=True))
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
    owner_id = Column(Integer, ForeignKey('user.id'))
    owner = relationship("User", back_populates="talks")
