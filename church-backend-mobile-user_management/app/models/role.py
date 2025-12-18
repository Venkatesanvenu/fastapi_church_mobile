"""
Role Model

Stores role information with permissions and active status.
Roles: ADMIN, PASTOR_STAFF, TEACHING_TEAM, COMMUNICATIONS_TEAM, SMALL_GROUP_LEADER
"""
from uuid import uuid4

from sqlalchemy import Boolean, Column, Enum, String, Text

from ..database import Base
from ..schemas.enums import UserRole


class Role(Base):
    """
    Role model - stores role information with permissions.
    
    Fields:
    - id: UUID primary key
    - role: Role enum value
    - permissions: JSON string or text describing permissions
    - is_active: Whether the role is currently active
    """
    __tablename__ = "role"

    # Primary key - UUID as string
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    
    # Role enum value
    role = Column(Enum(UserRole), nullable=False, unique=True, index=True)
    
    # Permissions - stored as text (can be JSON string or description)
    permissions = Column(Text, nullable=True)
    
    # Active status
    is_active = Column(Boolean, default=True, nullable=False)

