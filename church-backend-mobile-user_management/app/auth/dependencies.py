from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.user_management import UserManagement
from ..schemas.enums import UserRole
from .security import decode_token

security = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current authenticated user from either users or user_management table."""
    token = credentials.credentials
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    user_id = token_data["sub"]
    
    # First check users table
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.is_active:
        return user
    
    # Then check user_management table
    user_mgmt = db.query(UserManagement).filter(UserManagement.id == user_id).first()
    if user_mgmt and user_mgmt.is_active:
        return user_mgmt
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")


def require_roles(*roles: UserRole):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker

