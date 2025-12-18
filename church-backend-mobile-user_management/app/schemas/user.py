from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from .enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)


class UserCreate(UserBase):
    password: str  # No length restrictions
    role: Optional[UserRole] = None


class SubRoleUserCreate(UserBase):
    """Schema for Admin to create sub-role users (role is set automatically)."""
    password: str  # No length restrictions


class UserManagementCreate(BaseModel):
    """Schema for Lead Pastor to create users - password is auto-generated."""
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    role: UserRole  # Role assigned by Lead Pastor


class UserManagementResponse(BaseModel):
    """Response schema for UserManagement table."""
    id: str  # UUID as string
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    role_id: Optional[str] = None  # UUID as string
    permissions: Optional[str] = None

    class Config:
        from_attributes = True


class UserManagementUpdate(BaseModel):
    """Update schema for UserManagement."""
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    permissions: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    password: Optional[str] = None  # No length restrictions
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: str  # UUID as string
    role: UserRole
    is_active: bool
    created_by_id: Optional[str] = None  # UUID as string
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

