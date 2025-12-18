from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from ..auth.dependencies import require_roles
from ..auth.security import generate_secure_password, get_password_hash
from ..database import get_db
from ..models.user import User
from ..models.user_management import UserManagement
from ..models.role import Role
from ..schemas.auth import EmailNotification
from ..schemas.enums import UserRole
from ..schemas.user import (
    UserManagementCreate,
    UserManagementResponse,
    UserManagementUpdate,
)
from ..utils.email import send_email

router = APIRouter(prefix="/user_management", tags=["user_management"])


def send_user_credentials_email(
    background_tasks: BackgroundTasks,
    email: str,
    first_name: str,
    last_name: str,
    password: str,
    role: UserRole,
):
    """Send login credentials to newly created user."""
    role_name = role.value.replace("_", " ").title()
    notification = EmailNotification(
        recipient=email,
        subject=f"Your {role_name} Account Credentials",
        message=(
            f"Hello {first_name} {last_name},\n\n"
            f"Your {role_name} account has been created.\n\n"
            f"You can sign in using:\n\n"
            f"Email: {email}\n"
            f"Password: {password}\n"
            f"Role: {role_name}\n\n"
            f"Please keep these credentials secure and change your password after first login."
        ),
    )
    send_email(background_tasks, notification)


@router.post("/create", response_model=UserManagementResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserManagementCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Create a new user in user_management table. Only Lead Pastor (Admin) can create users for all roles.
    
    Stores: first_name, last_name, email, role in the user_management table.
    """
    # Check if email already exists in user_management table only
    # (This is a separate table from users, so we only check user_management)
    try:
        existing_mgmt = db.query(UserManagement).filter(UserManagement.email == payload.email).first()
        if existing_mgmt:
            # Get all emails in user_management for debugging
            all_emails = db.query(UserManagement.email).all()
            email_list = [email[0] for email in all_emails]
            raise HTTPException(
                status_code=400, 
                detail=f"Email '{payload.email}' already exists in user_management table. Existing emails: {email_list}"
            )
    except HTTPException:
        raise
    except Exception as e:
        # If query fails (e.g., table doesn't exist), let it fail at insert time
        # This will give a clearer error message
        pass
    
    # Validate that role is not SUPERADMIN (only system can create superadmin)
    if payload.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=400,
            detail="Cannot create superadmin users through this endpoint"
        )
    
    # Fetch role details from role table to get permissions and role_id
    role_details = db.query(Role).filter(Role.role == payload.role).first()
    if not role_details:
        raise HTTPException(
            status_code=404,
            detail=f"Role '{payload.role.value}' not found in role table. Please create the role first."
        )
    
    if not role_details.is_active:
        raise HTTPException(
            status_code=400,
            detail=f"Role '{payload.role.value}' is not active"
        )
    
    # Generate secure password for email notification
    generated_password = generate_secure_password()
    
    # Create user in user_management table - fetch permissions and role_id from role table
    # Store password hash so user can login
    user_mgmt = UserManagement(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        hashed_password=get_password_hash(generated_password),  # Store password hash for login
        role=payload.role,  # Role name stored in database as enum value
        role_id=role_details.id,  # Foreign key to role.id
        permissions=role_details.permissions,  # Fetch permissions from role table
        is_active=True,  # User is active by default
    )
    db.add(user_mgmt)
    db.commit()
    db.refresh(user_mgmt)
    
    # Send credentials via email
    send_user_credentials_email(
        background_tasks,
        payload.email,
        payload.first_name,
        payload.last_name,
        generated_password,
        payload.role,
    )
    
    return user_mgmt


@router.get("/list", response_model=List[UserManagementResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """List all users from user_management table. Only Lead Pastor (Admin) can view all users."""
    users = db.query(UserManagement).filter(UserManagement.role != UserRole.SUPERADMIN).all()
    return users


@router.get("/list/{role}", response_model=List[UserManagementResponse])
def list_users_by_role(
    role: UserRole = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """List users by role from user_management table. Only Lead Pastor (Admin) can view users."""
    # Prevent listing superadmin users
    if role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=403,
            detail="Cannot list superadmin users"
        )
    
    users = db.query(UserManagement).filter(UserManagement.role == role).all()
    return users


@router.get("/{user_id}", response_model=UserManagementResponse)
def get_user(
    user_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Get user by ID from user_management table. Only Lead Pastor (Admin) can view user details."""
    user = db.query(UserManagement).filter(UserManagement.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent viewing superadmin users
    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=403,
            detail="Cannot view superadmin user details"
        )
    
    return user


@router.put("/update/{user_id}", response_model=UserManagementResponse)
def update_user(
    user_id: str,
    payload: UserManagementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update user in user_management table. Only Lead Pastor (Admin) can update users."""
    user = db.query(UserManagement).filter(UserManagement.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent updating superadmin users
    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=403,
            detail="Cannot update superadmin users"
        )
    
    # Update fields if provided
    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.email is not None:
        # Check if new email already exists in user_management table
        existing_mgmt = db.query(UserManagement).filter(
            UserManagement.email == payload.email,
            UserManagement.id != user_id
        ).first()
        if existing_mgmt:
            raise HTTPException(
                status_code=400, 
                detail=f"Email '{payload.email}' already exists in user_management table"
            )
        
        # Also check if email exists in users table
        existing_user = db.query(User).filter(User.email == payload.email).first()
        if existing_user:
            raise HTTPException(
                status_code=400, 
                detail=f"Email '{payload.email}' already exists in users table"
            )
        
        user.email = payload.email
    if payload.role is not None:
        # Validate role exists in role table
        role_details = db.query(Role).filter(Role.role == payload.role).first()
        if not role_details:
            raise HTTPException(
                status_code=404,
                detail=f"Role '{payload.role.value}' not found in role table"
            )
        
        if not role_details.is_active:
            raise HTTPException(
                status_code=400,
                detail=f"Role '{payload.role.value}' is not active"
            )
        
        user.role = payload.role
        # Update role_id and permissions from role table
        user.role_id = role_details.id
        user.permissions = role_details.permissions
    
    # Update permissions if explicitly provided
    if payload.permissions is not None:
        user.permissions = payload.permissions
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete user from user_management table. Only Lead Pastor (Admin) can delete users."""
    user = db.query(UserManagement).filter(UserManagement.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting superadmin users
    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete superadmin users"
        )
    
    db.delete(user)
    db.commit()

