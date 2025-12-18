from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from ..database import Base

# Junction table for many-to-many relationship between Series and Sermon
series_sermons = Table(
    'series_sermons',
    Base.metadata,
    Column('series_id', String(36), ForeignKey('series.id', ondelete='CASCADE'), primary_key=True),
    Column('sermon_id', String(36), ForeignKey('sermons.id', ondelete='CASCADE'), primary_key=True)
)


class Series(Base):
    __tablename__ = "series"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    title = Column(String(255), nullable=False)
    from_date = Column(Date, nullable=False, index=True)
    to_date = Column(Date, nullable=False, index=True)
    passage = Column(String(255), nullable=False)  # Scripture reference
    description = Column(Text, nullable=False)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Many-to-many relationship with Sermon
    sermons = relationship("Sermon", secondary=series_sermons, back_populates="series", lazy="select")
    created_by = relationship("User", foreign_keys=[created_by_id])

