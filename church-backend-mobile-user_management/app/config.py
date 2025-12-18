from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError
import sys


# Get the project root directory (pastor_mobile folder)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str

    jwt_secret_key: str

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 30

    refresh_token_expire_days: int = 7

    otp_validity_minutes: int = 10

    smtp_server: str

    smtp_port: int

    smtp_username: str

    smtp_password: str

    from_email: str

    # Superadmin credentials
    superadmin_email: str
    superadmin_username: str
    superadmin_password: str

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Try to load settings, show helpful error if fails
try:
    settings = Settings()
    if ENV_FILE.exists():
        print(f"✅ Configuration loaded from: {ENV_FILE}")
    else:
        print(f"⚠️  .env file not found at: {ENV_FILE}")
        print("   Loading from environment variables only.")
except ValidationError as e:
    print("=" * 70)
    print("❌ CONFIGURATION ERROR: Missing or invalid environment variables")
    print("=" * 70)
    print(f"\n📁 Expected .env file location: {ENV_FILE}")
    print(f"📁 .env file exists: {ENV_FILE.exists()}\n")
    
    if not ENV_FILE.exists():
        print("💡 SOLUTION: Create a .env file in the pastor_mobile/ directory.")
        print("   Copy .env.example to .env and fill in the values.\n")
    else:
        print("Missing or invalid required environment variables:\n")
        missing_fields = set()
        for error in e.errors():
            field = error.get('loc', ['unknown'])[-1]
            missing_fields.add(field)
            msg = error.get('msg', 'Invalid value')
            print(f"  ❌ {field}: {msg}")
        
        print(f"\n💡 SOLUTION: Add these {len(missing_fields)} variables to your .env file:")
        for field in sorted(missing_fields):
            print(f"   {field}=your-value-here")
        print()
    
    print("📖 See .env.example for a template with all required variables.\n")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error loading configuration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

