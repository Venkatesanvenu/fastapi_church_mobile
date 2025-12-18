from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class DevotionalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    date: date
    passage: str = Field(..., min_length=1, max_length=255)
    leader: str = Field(..., min_length=1, max_length=255)
    sermon_id: Optional[str] = Field(None, description="Reference to sermon ID (UUID)")


class DevotionalCreate(DevotionalBase):
    """Schema for creating a new devotional."""
    pass


class DevotionalUpdate(BaseModel):
    """Schema for updating a devotional."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    date: Optional[date] = None
    passage: Optional[str] = Field(None, min_length=1, max_length=255)
    leader: Optional[str] = Field(None, min_length=1, max_length=255)
    sermon_id: Optional[str] = Field(None, description="Reference to sermon ID (UUID)")


class DevotionalResponse(DevotionalBase):
    """Schema for devotional response."""
    id: str  # UUID as string
    created_by_id: Optional[str] = None  # UUID as string
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DevotionalCountResponse(BaseModel):
    """Schema for devotional count response."""
    total: int

