from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from ..database import Base


class Devotional(Base):
    __tablename__ = "devotionals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    title = Column(String(255), nullable=False)
    date = Column(Date, nullable=False, index=True)
    passage = Column(String(255), nullable=False)
    leader = Column(String(255), nullable=False)
    sermon_id = Column(String(36), ForeignKey("sermons.id"), nullable=True)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by = relationship("User", foreign_keys=[created_by_id])
    sermon = relationship("Sermon", foreign_keys=[sermon_id])

