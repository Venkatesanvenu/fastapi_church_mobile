from datetime import date, datetime, time
from typing import Annotated, List, Optional

from pydantic import BaseModel, BeforeValidator, Field


def parse_time_string(v):
    """Parse time string in various formats to time object."""
    if v is None:
        return None
    if isinstance(v, time):
        return v
    if isinstance(v, str):
        # Try to parse various time formats
        v_upper = v.strip().upper()
        # Handle 12-hour format like "11:00 AM" or "2:30 PM"
        if 'AM' in v_upper or 'PM' in v_upper:
            is_pm = 'PM' in v_upper
            time_str = v_upper.replace('AM', '').replace('PM', '').strip()
            try:
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                second = int(parts[2]) if len(parts) > 2 else 0
                
                if is_pm and hour != 12:
                    hour += 12
                elif not is_pm and hour == 12:
                    hour = 0
                
                return time(hour, minute, second)
            except (ValueError, IndexError):
                raise ValueError(f"Invalid time format: {v}. Expected format: 'HH:MM AM/PM' or 'HH:MM:SS'")
        else:
            # Handle 24-hour format like "11:00" or "14:30:00"
            try:
                parts = v_upper.split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                second = int(parts[2]) if len(parts) > 2 else 0
                return time(hour, minute, second)
            except (ValueError, IndexError):
                raise ValueError(f"Invalid time format: {v}. Expected format: 'HH:MM' or 'HH:MM:SS'")
    raise ValueError(f"Time must be a string or time object, got {type(v)}")


TimeField = Annotated[Optional[time], BeforeValidator(parse_time_string)]


class SermonBase(BaseModel):
    date: date
    time: TimeField = None
    speaker: str = Field(..., min_length=1, max_length=255)
    passage: str = Field(..., min_length=1, max_length=255, description="Scripture reference like '1 Peter 2:1-10'")
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, description="The main idea/theme of the sermon")


class SermonCreate(SermonBase):
    """Schema for creating a new sermon."""
    pass


class SermonUpdate(BaseModel):
    """Schema for updating a sermon."""
    date: Optional[date] = None
    time: TimeField = None
    speaker: Optional[str] = Field(None, min_length=1, max_length=255)
    passage: Optional[str] = Field(None, min_length=1, max_length=255)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)


class SermonResponse(SermonBase):
    """Schema for sermon response."""
    id: str  # UUID as string
    created_by_id: Optional[str] = None  # UUID as string
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SermonCountResponse(BaseModel):
    """Schema for sermon count response."""
    total: int


class ExistingSeriesAssociate(BaseModel):
    """Schema for associating an existing series with a sermon."""
    series_id: str = Field(..., description="The ID (UUID) of the series to associate")


class ExistingSeriesResponse(BaseModel):
    """Schema for existing series response - unused series IDs for a sermon."""
    unused_series_ids: List[str] = Field(..., description="List of unused series IDs (UUIDs) available for the sermon")

