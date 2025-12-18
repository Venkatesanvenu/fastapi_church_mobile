from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from ..auth.dependencies import require_roles
from ..auth.security import get_password_hash
from ..database import get_db
from ..models.user import User
from ..schemas.auth import EmailNotification
from ..schemas.enums import UserRole
from ..schemas.user import UserCreate, UserResponse, UserUpdate
from ..utils.email import send_email

router = APIRouter(prefix="/admin", tags=["admin"])


def send_credentials_email(background_tasks: BackgroundTasks, email: str, password: str, role: UserRole = UserRole.ADMIN):
    role_name = role.value.replace("_", " ").title()
    notification = EmailNotification(
        recipient=email,
        subject=f"Your {role_name} Account Credentials",
        message=f"Welcome! Your {role_name} account has been created.\n\nYou can sign in using:\n\nEmail: {email}\nPassword: {password}\nRole: {role_name}",
    )
    send_email(background_tasks, notification)


@router.post("/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin(
    payload: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Create Admin user."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Force role to ADMIN
    raw_password = payload.password
    admin = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        hashed_password=get_password_hash(raw_password),
        role=UserRole.ADMIN,  # Always set to ADMIN
        created_by_id=current_user.id,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    send_credentials_email(background_tasks, payload.email, raw_password, UserRole.ADMIN)
    return admin


@router.get("/list", response_model=List[UserResponse])
def list_admins(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """List all Admin users."""
    admins = db.query(User).filter(User.role == UserRole.ADMIN).order_by(User.created_at.desc()).all()
    return admins


@router.get("/{user_id}", response_model=UserResponse)
def get_admin(
    user_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Get Admin user by ID."""
    admin = db.query(User).filter(User.id == user_id, User.role == UserRole.ADMIN).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin


@router.put("/update/{user_id}", response_model=UserResponse)
def update_admin(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update Admin user."""
    admin = db.query(User).filter(User.id == user_id, User.role == UserRole.ADMIN).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    if payload.first_name:
        admin.first_name = payload.first_name
    if payload.last_name:
        admin.last_name = payload.last_name
    if payload.password:
        admin.hashed_password = get_password_hash(payload.password)
    if payload.is_active is not None:
        admin.is_active = payload.is_active
    db.commit()
    db.refresh(admin)
    return admin


@router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete Admin user."""
    admin = db.query(User).filter(User.id == user_id, User.role == UserRole.ADMIN).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    db.delete(admin)
    db.commit()


@router.get("/me", response_model=UserResponse)
def get_current_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Get current authenticated admin user information."""
    return current_user


@router.put("/me/update", response_model=UserResponse)
def update_current_admin(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update current authenticated admin user profile."""
    if payload.first_name:
        current_user.first_name = payload.first_name
    if payload.last_name:
        current_user.last_name = payload.last_name
    if payload.password:
        current_user.hashed_password = get_password_hash(payload.password)
    if payload.is_active is not None:
        current_user.is_active = payload.is_active
    db.commit()
    db.refresh(current_user)
    return current_user
