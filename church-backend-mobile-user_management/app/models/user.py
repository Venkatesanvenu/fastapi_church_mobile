"""
User Management Model

This model represents all users in the system and supports the user_management functionality.
All user details including role are stored in the database.

Roles supported:
- SUPERADMIN: System superadmin
- ADMIN: Lead Pastor (can create users for all other roles)
- PASTOR_STAFF: Pastor / Staff
- TEACHING_TEAM: Teaching Team
- COMMUNICATIONS_TEAM: Communications Team
- SMALL_GROUP_LEADER: Small Group Leader
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from ..database import Base
from ..schemas.enums import UserRole


class User(Base):
    """
    User model for user management system.
    
    Stores all user information including:
    - Personal details (name, email)
    - Authentication (hashed password)
    - Role assignment (enum with all available roles)
    - Account status (active, verified)
    - OTP for verification/password reset
    - Audit trail (created_by, timestamps)
    """
    __tablename__ = "users"

    # Primary key - UUID as string
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    
    # User identification
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    
    # Role assignment - stored as enum value in database
    # Values: superadmin, admin, pastor_staff, teaching_team, communications_team, small_group_leader
    role = Column(Enum(UserRole), nullable=False, index=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # OTP for email verification and password reset
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    
    # Audit trail - tracks who created this user
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to track users created by this user
    created_users = relationship("User", remote_side=[id])

