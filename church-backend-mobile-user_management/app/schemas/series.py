from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from .sermon import SermonResponse


class SeriesBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    from_date: date
    to_date: date
    passage: str = Field(..., min_length=1, max_length=255, description="Scripture reference")
    description: str = Field(..., min_length=1)


class SeriesCreate(BaseModel):
    """Schema for creating a new series."""
    title: str = Field(..., min_length=1, max_length=255)
    from_date: date
    to_date: date
    passage: str = Field(..., min_length=1, max_length=255, description="Scripture reference")
    description: str = Field(..., min_length=1)
    sermons_id: Optional[List[str]] = Field(None, description="List of Sermon IDs (UUIDs) to link to this series")


class SeriesUpdate(BaseModel):
    """Schema for updating a series."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    passage: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)


class SeriesResponse(SeriesBase):
    """Schema for series response."""
    id: str  # UUID as string
    created_by_id: Optional[str] = None  # Admin user ID (UUID)
    created_at: datetime
    updated_at: datetime
    sermons: List[SermonResponse] = []  # List of sermons

    @computed_field
    @property
    def sermons_count(self) -> int:
        """Count of sermons in the series."""
        return len(self.sermons)

    class Config:
        from_attributes = True


class SeriesCreateResponse(BaseModel):
    """Schema for series create response with full sermon details."""
    id: str  # UUID as string
    title: str
    from_date: date
    to_date: date
    passage: str
    description: str
    created_by_id: Optional[str] = None  # Admin user ID (UUID)
    created_at: datetime
    updated_at: datetime
    sermons: List[SermonResponse] = []  # List of full sermon details

    class Config:
        from_attributes = True


class SeriesInsertSermons(BaseModel):
    """Schema for inserting sermons into an existing series."""
    sermons_id: List[str] = Field(..., min_items=1, description="List of Sermon IDs (UUIDs) to add to this series")


class SeriesDeleteSermons(BaseModel):
    """Schema for deleting sermons from an existing series."""
    sermons_id: List[str] = Field(..., min_items=1, description="List of Sermon IDs (UUIDs) to remove from this series")


class SeriesDetailResponse(SeriesBase):
    """Schema for series detail response with access and available sermons."""
    id: str  # UUID as string
    created_by_id: Optional[str] = None  # Admin user ID (UUID)
    created_at: datetime
    updated_at: datetime
    access_sermons: List[SermonResponse] = []  # Sermons that are in this series
    available_sermons: List[SermonResponse] = []  # Sermons that are NOT in this series

    class Config:
        from_attributes = True


class SeriesSermonsResponse(BaseModel):
    """Schema for series sermons response with only access and available sermons."""
    access_sermons: List[SermonResponse] = []  # Sermons that are in this series
    available_sermons: List[SermonResponse] = []  # Sermons that are NOT in this series


class SeriesCountResponse(BaseModel):
    """Schema for series count response."""
    total: int

