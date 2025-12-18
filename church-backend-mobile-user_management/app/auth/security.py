from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..config import settings
from ..models.user import User
from ..models.user_management import UserManagement

# Configure bcrypt to handle longer passwords by truncating internally
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",  # Use bcrypt 2b format
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    # Truncate password to 72 bytes if longer (bcrypt limit)
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        plain_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    # Truncate password to 72 bytes if longer (bcrypt limit)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode = {"exp": expire, "sub": subject, "role": role}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def authenticate_user(db: Session, email: str, password: str):
    """Authenticate user from either users or user_management table.
    
    Returns User or UserManagement object if authenticated, None otherwise.
    """
    # First check users table
    user = db.query(User).filter(User.email == email).first()
    if user:
        if not user.is_active:
            return None
        if not user.hashed_password:
            return None
        if verify_password(password, user.hashed_password):
            return user
    
    # Then check user_management table
    user_mgmt = db.query(UserManagement).filter(UserManagement.email == email).first()
    if user_mgmt:
        if not user_mgmt.is_active:
            return None
        if not user_mgmt.hashed_password:
            # User exists but has no password set - they need to reset password
            return None
        if verify_password(password, user_mgmt.hashed_password):
            return user_mgmt
    
    return None


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def create_refresh_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT-based refresh token (no database storage)."""
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.refresh_token_expire_days))
    to_encode = {"exp": expire, "sub": subject, "role": role, "type": "refresh"}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_refresh_token(token: str) -> Optional[dict]:
    """Verify a refresh token and return decoded payload if valid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def generate_otp() -> str:
    """Generate a 6-digit OTP code."""
    import random
    return str(random.randint(100000, 999999))


def generate_secure_password(length: int = 12) -> str:
    """Generate a secure random password with uppercase, lowercase, digits, and special characters.
    
    Example output: 7dsW3847#$n
    """
    import secrets
    import string
    
    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Ensure at least one character from each set
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]
    
    # Fill the rest with random characters from all sets
    all_chars = uppercase + lowercase + digits + special
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Shuffle to avoid predictable pattern using secrets
    # Convert to list, shuffle indices, then rebuild
    indices = list(range(len(password)))
    shuffled_indices = []
    while indices:
        idx = secrets.randbelow(len(indices))
        shuffled_indices.append(indices.pop(idx))
    
    shuffled_password = [password[i] for i in shuffled_indices]
    return ''.join(shuffled_password)


def is_otp_valid(otp_code: str, stored_otp: Optional[str], otp_expires_at: Optional[datetime]) -> bool:
    """Check if OTP is valid and not expired."""
    if not otp_code or not stored_otp or not otp_expires_at:
        return False
    if otp_code != stored_otp:
        return False
    if datetime.utcnow() > otp_expires_at:
        return False
    return True