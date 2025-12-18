from datetime import date, datetime, time
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text, Time
from sqlalchemy.orm import relationship

from ..database import Base


class Sermon(Base):
    __tablename__ = "sermons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    date = Column(Date, nullable=False, index=True)
    time = Column(Time, nullable=True)
    speaker = Column(String(255), nullable=False)
    passage = Column(String(255), nullable=False)  # Scripture reference like "1 Peter 2:1-10"
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)  # The main idea/theme of the sermon
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by = relationship("User", foreign_keys=[created_by_id])
    series = relationship("Series", secondary="series_sermons", back_populates="sermons", lazy="select")

