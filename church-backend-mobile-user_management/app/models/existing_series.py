from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint

from ..database import Base


class ExistingSeries(Base):
    __tablename__ = "existing_series"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    sermon_id = Column(String(36), ForeignKey("sermons.id", ondelete="CASCADE"), nullable=False, index=True)
    series_id = Column(String(36), ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint('sermon_id', 'series_id', name='uq_existing_series_sermon_series'),
    )
