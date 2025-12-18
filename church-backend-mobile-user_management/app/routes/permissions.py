"""
Permissions Routes

API endpoints for managing user permissions from user_management table.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from ..auth.dependencies import require_roles
from ..database import get_db
from ..models.user import User
from ..models.user_management import UserManagement
from ..schemas.enums import UserRole
from ..schemas.permissions import PermissionResponse, PermissionUpdate

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("/list", response_model=List[PermissionResponse])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """List all users with their permissions from user_management table.
    
    Only Lead Pastor (Admin) can view all permissions.
    """
    users = db.query(UserManagement).filter(
        UserManagement.role != UserRole.SUPERADMIN
    ).order_by(UserManagement.email).all()
    
    return [
        PermissionResponse(
            user_id=user.id,
            user_email=user.email,
            user_name=f"{user.first_name} {user.last_name}",
            role=user.role.value,
            permissions=user.permissions,
        )
        for user in users
    ]


@router.get("/list/{user_id}", response_model=PermissionResponse)
def get_user_permissions(
    user_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Get permissions for a specific user from user_management table.
    
    Only Lead Pastor (Admin) can view user permissions.
    """
    user = db.query(UserManagement).filter(UserManagement.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with ID '{user_id}' not found in user_management table"
        )
    
    # Prevent viewing superadmin permissions
    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=403,
            detail="Cannot view superadmin permissions"
        )
    
    return PermissionResponse(
        user_id=user.id,
        user_email=user.email,
        user_name=f"{user.first_name} {user.last_name}",
        role=user.role.value,
        permissions=user.permissions,
    )


@router.put("/update/{user_id}", response_model=PermissionResponse)
def update_permissions(
    user_id: str,
    payload: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update permissions for a user in user_management table.
    
    Only Lead Pastor (Admin) can update permissions.
    """
    user = db.query(UserManagement).filter(UserManagement.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with ID '{user_id}' not found in user_management table"
        )
    
    # Prevent updating superadmin permissions
    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=403,
            detail="Cannot update superadmin permissions"
        )
    
    # Update permissions
    user.permissions = payload.permissions
    db.commit()
    db.refresh(user)
    
    return PermissionResponse(
        user_id=user.id,
        user_email=user.email,
        user_name=f"{user.first_name} {user.last_name}",
        role=user.role.value,
        permissions=user.permissions,
    )


@router.get("/by-role/{role}", response_model=List[PermissionResponse])
def list_permissions_by_role(
    role: UserRole = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """List permissions for all users with a specific role.
    
    Only Lead Pastor (Admin) can view permissions by role.
    """
    # Prevent listing superadmin permissions
    if role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=403,
            detail="Cannot list superadmin permissions"
        )
    
    users = db.query(UserManagement).filter(UserManagement.role == role).all()
    
    return [
        PermissionResponse(
            user_id=user.id,
            user_email=user.email,
            user_name=f"{user.first_name} {user.last_name}",
            role=user.role.value,
            permissions=user.permissions,
        )
        for user in users
    ]

