from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from .enums import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    first_name: str
    last_name: str
    role: UserRole
    permissions: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AdminSignupRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class AdminSignupResponse(BaseModel):
    message: str
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str


class VerifyOTPResponse(BaseModel):
    message: str
    is_verified: bool


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    message: str


class ResendOTPRequest(BaseModel):
    email: EmailStr


class ResendOTPResponse(BaseModel):
    message: str


class EmailNotification(BaseModel):
    recipient: EmailStr
    subject: str
    message: str
    sent_at: Optional[datetime] = None

