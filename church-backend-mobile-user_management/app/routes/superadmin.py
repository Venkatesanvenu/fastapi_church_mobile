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

router = APIRouter(prefix="/superadmin", tags=["superadmin"])


def send_credentials_email(background_tasks: BackgroundTasks, email: str, password: str, role: UserRole = UserRole.ADMIN):
    role_name = role.value.replace("_", " ").title()
    notification = EmailNotification(
        recipient=email,
        subject=f"Your {role_name} Account Credentials",
        message=f"Welcome! Your {role_name} account has been created.\n\nYou can sign in using:\n\nEmail: {email}\nPassword: {password}\nRole: {role_name}",
    )
    send_email(background_tasks, notification)


@router.get("/admins/list", response_model=List[UserResponse])
def list_admins(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    """List Admins."""
    admins = db.query(User).filter(User.role == UserRole.ADMIN).order_by(User.created_at.desc()).all()
    return admins


@router.post("/admins/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin(
    payload: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    """Create Admin - Superadmin can only create Admin role users."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Force role to ADMIN (superadmin can only create admins)
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

    send_credentials_email(background_tasks, payload.email, raw_password)
    
    # Return admin with role explicitly included in response
    return admin


@router.get("/admins/count")
def count_admins(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    """Count Admins."""
    count = db.query(User).filter(User.role == UserRole.ADMIN).count()
    return {"count": count}


@router.get("/admins/{admin_id}", response_model=UserResponse)
def get_admin(
    admin_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    """Get Admin."""
    admin = db.query(User).filter(User.id == admin_id, User.role == UserRole.ADMIN).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin


@router.put("/admins/update/{admin_id}", response_model=UserResponse)
def update_admin(
    admin_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    """Update Admin."""
    admin = db.query(User).filter(User.id == admin_id, User.role == UserRole.ADMIN).first()
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


@router.delete("/admins/delete/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    """Delete Admin."""
    admin = db.query(User).filter(User.id == admin_id, User.role == UserRole.ADMIN).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    db.delete(admin)
    db.commit()

