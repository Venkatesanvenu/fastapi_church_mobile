from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth.security import create_access_token, create_refresh_token, verify_refresh_token
from ..config import settings
from ..database import get_db
from ..models.user import User
from ..models.user_management import UserManagement
from ..schemas.auth import RefreshTokenRequest, RefreshTokenResponse

router = APIRouter(prefix="/refresh", tags=["Refresh Token"])


@router.post("/", response_model=RefreshTokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    
    This endpoint allows users to get a new access token when their current one expires,
    without needing to log in again. The refresh token must be valid and not expired.
    
    Returns a new access token and a new refresh token (token rotation for security).
    """
    # Verify the refresh token
    refresh_token_payload = verify_refresh_token(payload.refresh_token)
    if not refresh_token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired refresh token"
        )
    
    # Extract user ID from refresh token (UUID as string)
    user_id = refresh_token_payload["sub"]
    
    # Verify user exists and is active (check both tables)
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        # Check user_management table
        user = db.query(UserManagement).filter(UserManagement.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="User not found or inactive"
            )
    
    # Create new access token
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    
    # Create new refresh token (token rotation for security)
    new_refresh_token = create_refresh_token(
        subject=str(user.id),
        role=user.role.value,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    
    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )

