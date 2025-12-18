"""
User Management Model

Separate table for user management with simplified fields:
- first_name
- last_name  
- email
- role (references role table)
- permissions (fetched from role table)

This table stores user information specifically for user management purposes.
"""
from uuid import uuid4

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from ..database import Base
from ..schemas.enums import UserRole


class UserManagement(Base):
    """
    User Management model - simplified user table.
    
    Stores essential user information for user management:
    - Personal details (first_name, last_name, email)
    - Role assignment (references role table)
    - Permissions (fetched from role table via relationship)
    
    This is a separate table from the main User model.
    """
    __tablename__ = "user_management"

    # Primary key - UUID as string
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    
    # User identification
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Authentication - password hash for login
    hashed_password = Column(String(255), nullable=True)
    
    # Role assignment - enum value that matches role table
    role = Column(Enum(UserRole), nullable=False, index=True)
    
    # Role ID - foreign key to role.id
    role_id = Column(String(36), ForeignKey('role.id'), nullable=True, index=True)
    
    # Permissions - fetched from role table and stored here
    permissions = Column(Text, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationship to Role table via role_id
    role_details = relationship("Role", foreign_keys=[role_id], uselist=False)

