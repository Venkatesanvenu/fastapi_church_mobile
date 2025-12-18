from datetime import timedelta, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..auth.security import (
    authenticate_user, create_access_token, create_refresh_token,
    generate_otp, get_password_hash, is_otp_valid
)
from ..config import settings
from ..database import get_db
from ..models.user import User
from ..schemas.auth import (
    AdminSignupRequest, AdminSignupResponse, ForgotPasswordRequest,
    ForgotPasswordResponse, LoginRequest, LoginResponse, ResendOTPRequest,
    ResendOTPResponse, ResetPasswordRequest, ResetPasswordResponse,
    Token, VerifyOTPRequest, VerifyOTPResponse, EmailNotification
)
from ..schemas.enums import UserRole
from ..schemas.user import UserResponse
from ..utils.email import send_email

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/superadmin/login", response_model=LoginResponse)
def superadmin_login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Superadmin Login - Only accepts superadmin credentials from settings."""
    # Use superadmin credentials from settings
    if payload.email != settings.superadmin_email or payload.password != settings.superadmin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    user = db.query(User).filter(User.email == settings.superadmin_email, User.role == UserRole.SUPERADMIN).first()
    
    # If superadmin doesn't exist, create it
    if not user:
        from ..auth.security import get_password_hash
        user = User(
            email=settings.superadmin_email,
            first_name="super",
            last_name="admin",
            hashed_password=get_password_hash(settings.superadmin_password),
            role=UserRole.SUPERADMIN,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Get permissions from role table for superadmin
    from ..models.role import Role
    permissions = None
    role_details = db.query(Role).filter(Role.role == user.role).first()
    if role_details:
        permissions = role_details.permissions
    
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        role=user.role.value,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        permissions=permissions,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Account Login - General login endpoint for all roles. Accepts JSON with email and password.
    
    Supports login from both users and user_management tables.
    """
    from ..models.user_management import UserManagement
    
    # Check if user exists in either table
    user_in_users = db.query(User).filter(User.email == payload.email).first()
    user_in_mgmt = db.query(UserManagement).filter(UserManagement.email == payload.email).first()
    
    # Provide more specific error messages
    if not user_in_users and not user_in_mgmt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials - Email not found")
    
    # Check if user exists but has no password (created before password storage was added)
    if user_in_mgmt and not user_in_mgmt.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Account exists but password not set. Please contact administrator to reset your password."
        )
    
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        # More specific error - password might be wrong or account inactive
        if user_in_users and not user_in_users.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
        if user_in_mgmt and not user_in_mgmt.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials - Incorrect password")
    
    # Superadmin should use /superadmin/login endpoint
    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Use /auth/superadmin/login endpoint")
    
    # Check if admin is verified (only for User model, not UserManagement)
    if isinstance(user, User) and user.role == UserRole.ADMIN and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified. Please verify your account using the OTP code sent to your email."
        )
    
    # Get permissions - from user_management table if UserManagement, or None for User
    permissions = None
    if isinstance(user, UserManagement):
        permissions = user.permissions
    elif isinstance(user, User):
        # For User model, try to fetch from role table
        from ..models.role import Role
        role_details = db.query(Role).filter(Role.role == user.role).first()
        if role_details:
            permissions = role_details.permissions
    
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        role=user.role.value,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        first_name=user.first_name,
        last_name=user.last_name if hasattr(user, 'last_name') else "",
        role=user.role,
        permissions=permissions,
    )


@router.post("/admin/signup", response_model=AdminSignupResponse, status_code=status.HTTP_201_CREATED)
def admin_signup(
    payload: AdminSignupRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Admin signup - Create a new admin account."""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Generate OTP
    otp_code = generate_otp()
    otp_expires_at = datetime.utcnow() + timedelta(minutes=settings.otp_validity_minutes)
    
    # Create admin user
    admin_user = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=False,
        otp_code=otp_code,
        otp_expires_at=otp_expires_at,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # Send OTP email
    notification = EmailNotification(
        recipient=payload.email,
        subject="Admin Account Verification - OTP Code",
        message=f"Welcome! Your admin account has been created.\n\nYour OTP code is: {otp_code}\n\nThis code will expire in {settings.otp_validity_minutes} minutes.\n\nPlease verify your account using this OTP code.",
    )
    send_email(background_tasks, notification)
    
    return AdminSignupResponse(
        message="Admin account created successfully. Please check your email for OTP verification code.",
        email=payload.email
    )


@router.post("/admin/forgot-password", response_model=ForgotPasswordResponse)
def admin_forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Admin forgot password - Send OTP to reset password."""
    user = db.query(User).filter(
        User.email == payload.email,
        User.role == UserRole.ADMIN
    ).first()
    
    if not user:
        # Don't reveal if email exists for security
        return ForgotPasswordResponse(
            message="If the email exists, an OTP code has been sent."
        )
    
    # Generate new OTP
    otp_code = generate_otp()
    otp_expires_at = datetime.utcnow() + timedelta(minutes=settings.otp_validity_minutes)
    
    # Update user with new OTP
    user.otp_code = otp_code
    user.otp_expires_at = otp_expires_at
    db.commit()
    
    # Send OTP email
    notification = EmailNotification(
        recipient=payload.email,
        subject="Password Reset - OTP Code",
        message=f"You requested to reset your password.\n\nYour OTP code is: {otp_code}\n\nThis code will expire in {settings.otp_validity_minutes} minutes.\n\nIf you didn't request this, please ignore this email.",
    )
    send_email(background_tasks, notification)
    
    return ForgotPasswordResponse(
        message="If the email exists, an OTP code has been sent."
    )


@router.post("/admin/verify-otp", response_model=VerifyOTPResponse)
def admin_verify_otp(
    payload: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """Admin verify OTP - Verify OTP code for account verification."""
    user = db.query(User).filter(
        User.email == payload.email,
        User.role == UserRole.ADMIN
    ).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Verify OTP
    if not is_otp_valid(payload.otp_code, user.otp_code, user.otp_expires_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP code")
    
    # Mark as verified and clear OTP
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    
    return VerifyOTPResponse(
        message="Account verified successfully",
        is_verified=True
    )


@router.post("/admin/reset-password", response_model=ResetPasswordResponse)
def admin_reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Admin reset password - Reset password using OTP code."""
    user = db.query(User).filter(
        User.email == payload.email,
        User.role == UserRole.ADMIN
    ).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Verify OTP
    if not is_otp_valid(payload.otp_code, user.otp_code, user.otp_expires_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP code")
    
    # Update password and clear OTP
    user.hashed_password = get_password_hash(payload.new_password)
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    
    return ResetPasswordResponse(
        message="Password reset successfully"
    )


@router.post("/admin/resend-otp", response_model=ResendOTPResponse)
def admin_resend_otp(
    payload: ResendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Admin resend OTP - Resend OTP code for verification."""
    user = db.query(User).filter(
        User.email == payload.email,
        User.role == UserRole.ADMIN
    ).first()
    
    if not user:
        # Don't reveal if email exists for security
        return ResendOTPResponse(
            message="If the email exists, an OTP code has been sent."
        )
    
    # Generate new OTP
    otp_code = generate_otp()
    otp_expires_at = datetime.utcnow() + timedelta(minutes=settings.otp_validity_minutes)
    
    # Update user with new OTP
    user.otp_code = otp_code
    user.otp_expires_at = otp_expires_at
    db.commit()
    
    # Send OTP email
    notification = EmailNotification(
        recipient=payload.email,
        subject="OTP Code - Account Verification",
        message=f"Your OTP code is: {otp_code}\n\nThis code will expire in {settings.otp_validity_minutes} minutes.\n\nPlease use this code to verify your account.",
    )
    send_email(background_tasks, notification)
    
    return ResendOTPResponse(
        message="If the email exists, an OTP code has been sent."
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user

