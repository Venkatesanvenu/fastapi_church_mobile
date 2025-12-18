"""
Role Schemas

Schemas for Role model operations.
"""
from typing import Optional

from pydantic import BaseModel, Field

from .enums import UserRole


class RoleBase(BaseModel):
    """Base schema for Role."""
    role: UserRole
    permissions: Optional[str] = None
    is_active: bool = True


class RoleCreate(RoleBase):
    """Schema for creating a new role."""
    pass


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    permissions: Optional[str] = Field(default=None, description="Permissions description or JSON")
    is_active: Optional[bool] = Field(default=None, description="Whether the role is active")


class RoleResponse(RoleBase):
    """Response schema for Role."""
    id: str  # UUID as string

    class Config:
        from_attributes = True

