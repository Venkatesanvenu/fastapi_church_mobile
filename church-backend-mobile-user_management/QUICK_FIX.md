# 🚀 Quick Fix Guide - Blank Page Issue

## The Problem
Your FastAPI app shows a **blank page** at `127.0.0.1:8000` because it's **crashing during startup** due to a missing `.env` file.

## The Solution (2 Minutes)

### Step 1: Create .env File
Create a file named `.env` in the `pastor_mobile/` directory with this content:

```env
DATABASE_URL=sqlite:///./pastor_mobile.db
JWT_SECRET_KEY=your-super-secret-key-change-this-minimum-32-characters-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
OTP_VALIDITY_MINUTES=10
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
SUPERADMIN_EMAIL=superadmin@gmail.com
SUPERADMIN_USERNAME=superadmin
SUPERADMIN_PASSWORD=superadmin@123
```

### Step 2: Start Your Server
```bash
cd pastor_mobile
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 3: Test
- Open: `http://127.0.0.1:8000` → Should show JSON response
- Open: `http://127.0.0.1:8000/docs` → Should show Swagger UI

## What I Fixed

✅ **Improved error messages** - Now shows exactly what's missing  
✅ **Removed hard-coded credentials** - Now uses settings from .env  
✅ **Better startup handling** - Clearer error messages if .env is missing  

## Files Changed
- `app/config.py` - Better error handling
- `app/main.py` - Uses settings instead of hard-coded values
- `app/routes/auth.py` - Uses settings instead of hard-coded values

## Still Need Help?
See `STARTUP_ISSUES.md` for detailed analysis.

