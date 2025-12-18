from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, SessionLocal
from .models.user import User
from .routes import admin as admin_routes
from .routes import auth as auth_routes
from .routes import devotional as devotional_routes
from .routes import refresh as refresh_routes
from .routes import sermons as sermons_routes
from .routes import series as series_routes
from .routes import superadmin as superadmin_routes
from .routes import user_management as user_management_routes
from .routes import permissions as permissions_routes
from .schemas.enums import UserRole
from .auth.security import get_password_hash

Base.metadata.create_all(bind=engine)


def init_superadmin():
    """Initialize superadmin with hard-coded credentials if it doesn't exist."""
    db: Session = SessionLocal()
    try:
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        
        # Debug: Print database URL (without password)
        db_url_display = settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url
        print(f"🔍 Checking database: {db_url_display}")
        
        # Check total users count for debugging
        total_users = db.query(User).count()
        print(f"🔍 Total users in database: {total_users}")
        
        # Check if superadmin already exists (by email AND role)
        existing = db.query(User).filter(
            User.email == settings.superadmin_email,
            User.role == UserRole.SUPERADMIN
        ).first()
        if existing:
            print("ℹ️  Superadmin already exists in database")
            return
        
        # Create superadmin
        superadmin = User(
            email=settings.superadmin_email,
            first_name="super",
            last_name="admin",
            hashed_password=get_password_hash(settings.superadmin_password),
            role=UserRole.SUPERADMIN,
            is_active=True,
        )
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)
        print("✅ Superadmin initialized successfully!")
        print(f"   Email: {settings.superadmin_email}")
        print(f"   Password: {settings.superadmin_password}")
    except Exception as e:
        print(f"⚠️  Error initializing superadmin: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


# Initialize superadmin on startup
init_superadmin()

app = FastAPI(
    title="Pastor Mobile API",
    version="1.0.0",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": False,
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(refresh_routes.router, prefix="/api/v1")
app.include_router(superadmin_routes.router, prefix="/api/v1")
app.include_router(admin_routes.router, prefix="/api/v1")
app.include_router(user_management_routes.router, prefix="/api/v1")
app.include_router(permissions_routes.router, prefix="/api/v1")
app.include_router(sermons_routes.router, prefix="/api/v1")
app.include_router(series_routes.router, prefix="/api/v1")
app.include_router(devotional_routes.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root():
    """Root endpoint - API information."""
    return {
        "message": "Pastor Mobile API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

