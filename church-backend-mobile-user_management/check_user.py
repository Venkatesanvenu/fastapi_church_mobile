"""
Quick script to check user status in database.
Run this to diagnose login issues.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.models.user_management import UserManagement

def check_user(email: str):
    db = SessionLocal()
    try:
        print(f"\n🔍 Checking user: {email}\n")
        
        # Check users table
        user = db.query(User).filter(User.email == email).first()
        if user:
            print("✅ Found in 'users' table:")
            print(f"   ID: {user.id}")
            print(f"   Name: {user.first_name} {user.last_name}")
            print(f"   Role: {user.role.value}")
            print(f"   Is Active: {user.is_active}")
            print(f"   Has Password: {'Yes' if user.hashed_password else 'No'}")
            if user.hashed_password:
                print(f"   Password Hash: {user.hashed_password[:20]}...")
            return
        
        # Check user_management table
        user_mgmt = db.query(UserManagement).filter(UserManagement.email == email).first()
        if user_mgmt:
            print("✅ Found in 'user_management' table:")
            print(f"   ID: {user_mgmt.id}")
            print(f"   Name: {user_mgmt.first_name} {user_mgmt.last_name}")
            print(f"   Role: {user_mgmt.role.value}")
            print(f"   Is Active: {user_mgmt.is_active}")
            print(f"   Has Password: {'Yes' if user_mgmt.hashed_password else 'No'}")
            if user_mgmt.hashed_password:
                print(f"   Password Hash: {user_mgmt.hashed_password[:20]}...")
            else:
                print("\n⚠️  WARNING: User has no password set!")
                print("   This user was likely created before password storage was added.")
                print("   You need to update their password.")
            return
        
        print("❌ User not found in either table")
        
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_user.py <email>")
        sys.exit(1)
    
    check_user(sys.argv[1])

