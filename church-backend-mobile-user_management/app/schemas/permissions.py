"""
Permissions Schemas

Schemas for permissions management operations.
"""
from typing import Optional

from pydantic import BaseModel, Field


class PermissionUpdate(BaseModel):
    """Schema for updating permissions."""
    permissions: str = Field(..., min_length=1, description="Permissions description or JSON")


class PermissionResponse(BaseModel):
    """Response schema for permissions."""
    user_id: str
    user_email: str
    user_name: str  # first_name + last_name
    role: str
    permissions: Optional[str] = None

    class Config:
        from_attributes = True

