# Role-Based Authentication System - Analysis

## 📋 Requirements Overview

### **Five Roles in the System:**

1. **Superadmin** (Primary Role)
   - Hard-coded credentials in application
   - Email: `superadmin@gmail.com`
   - Username: `superadmin`
   - Password: `superadmin@123`
   - Only role that can sign in initially
   - Creates Admin accounts
   - Sends login credentials to Admins via email

2. **Admin** (Secondary Role)
   - Cannot self-register (created by Superadmin)
   - Receives credentials via email from Superadmin
   - Can create three sub-roles:
     - Teaching
     - Publishing
     - Small Groups
   - Sends login credentials to sub-roles via email

3. **Teaching** (Sub-role)
   - Cannot self-register (created by Admin)
   - Receives credentials via email from Admin

4. **Publishing** (Sub-role)
   - Cannot self-register (created by Admin)
   - Receives credentials via email from Admin

5. **Small Groups** (Sub-role)
   - Cannot self-register (created by Admin)
   - Receives credentials via email from Admin

---

## 🔐 CRUD Permissions Matrix

| Role | Create | Read | Update | Delete |
|------|--------|------|--------|--------|
| **Superadmin** | Admin | Admin | Admin | Admin |
| **Admin** | Teaching, Publishing, Small Groups | All | Teaching, Publishing, Small Groups | Teaching, Publishing, Small Groups |
| **Teaching** | ❌ | ✔ | ✔ (own profile only) | ❌ |
| **Publishing** | ❌ | ✔ | ✔ (own profile only) | ❌ |
| **Small Groups** | ❌ | ✔ | ✔ (own profile only) | ❌ |

---

## 🛣️ API Endpoint Structure

### **Authentication Endpoints** (`/auth`)

1. `POST /auth/superadmin/login`
   - Superadmin login endpoint
   - Returns JWT token
   - Only accepts Superadmin credentials

2. `POST /auth/login`
   - General login endpoint
   - For Admin, Teaching, Publishing, Small Groups
   - Returns JWT token

3. `POST /auth/me`
   - Get current authenticated user info
   - Requires valid JWT token

### **Superadmin Routes** (`/superadmin`)

Full CRUD operations for Admin management:

1. `GET /superadmin/admins`
   - List all Admins
   - Requires Superadmin role

2. `POST /superadmin/admins`
   - Create new Admin
   - Sends credentials via email
   - Requires Superadmin role

3. `GET /superadmin/admins/{admin_id}`
   - Get Admin by ID
   - Requires Superadmin role

4. `GET /superadmin/admins/count`
   - Count total Admins
   - Requires Superadmin role

5. `PUT /superadmin/admins/{admin_id}`
   - Update Admin
   - Requires Superadmin role

6. `DELETE /superadmin/admins/{admin_id}`
   - Delete Admin
   - Requires Superadmin role

### **Admin Routes** (`/admin`)

CRUD operations for Teaching, Publishing, and Small Groups:

1. `GET /admin/teaching`
   - List all Teaching users
   - Requires Admin role

2. `GET /admin/teaching/{user_id}`
   - Get Teaching user by ID
   - Requires Admin role

3. `POST /admin/teaching`
   - Create Teaching user
   - Sends credentials via email
   - Requires Admin role

4. `PUT /admin/teaching/{user_id}`
   - Update Teaching user
   - Requires Admin role

5. `GET /admin/publishing`
   - List all Publishing users
   - Requires Admin role

6. `GET /admin/publishing/{user_id}`
   - Get Publishing user by ID
   - Requires Admin role

7. `POST /admin/publishing`
   - Create Publishing user
   - Sends credentials via email
   - Requires Admin role

8. `PUT /admin/publishing/{user_id}`
   - Update Publishing user
   - Requires Admin role

9. `GET /admin/small_groups`
   - List all Small Groups users
   - Requires Admin role

10. `GET /admin/small_groups/{user_id}`
    - Get Small Groups user by ID
    - Requires Admin role

11. `POST /admin/small_groups`
    - Create Small Groups user
    - Sends credentials via email
    - Requires Admin role

12. `PUT /admin/small_groups/{user_id}`
    - Update Small Groups user
    - Requires Admin role

### **User Self-Management Routes** (`/user`)

For Teaching, Publishing, and Small Groups to manage their own profiles:

1. `GET /user/me`
   - Get own profile
   - Requires authentication

2. `PUT /user/me`
   - Update own profile
   - Requires authentication
   - Can only update own profile

---

## 🗄️ Database Schema

### **User Model**

```python
class User:
    id: int (Primary Key)
    email: str (Unique, Indexed)
    first_name: str
    last_name: str
    hashed_password: str
    role: Enum (SUPERADMIN, ADMIN, TEACHING, PUBLISHING, SMALL_GROUPS)
    is_active: bool (default: True)
    created_by_id: int (ForeignKey to User.id, nullable)
    created_at: datetime
    updated_at: datetime
```

---

## 🔧 Technical Implementation Details

### **Authentication Flow:**

1. **Superadmin Login:**
   - Check hard-coded credentials
   - Generate JWT token with role claim
   - Return token

2. **Other Roles Login:**
   - Verify email/password
   - Check if user is active
   - Generate JWT token with role claim
   - Return token

3. **JWT Token Structure:**
   ```json
   {
     "sub": "user_id",
     "role": "superadmin|admin|teaching|publishing|small_groups",
     "exp": "expiration_timestamp"
   }
   ```

### **Authorization Middleware:**

- Extract JWT token from Authorization header
- Verify token signature
- Decode user ID and role
- Check role permissions for requested endpoint
- Allow/deny access based on permissions

### **Email Service:**

- Send credentials email when:
  - Superadmin creates Admin
  - Admin creates Teaching/Publishing/Small Groups user
- Email contains:
  - Email address
  - Generated password
  - Login instructions

---

## 📦 Required Dependencies

✅ Already in requirements.txt:
- FastAPI
- SQLAlchemy
- Alembic
- python-jose (JWT)
- passlib[bcrypt] (Password hashing)
- pydantic-settings
- email-validator
- psycopg2-binary (PostgreSQL)

---

## 🏗️ Project Structure

```
pastor_mobile/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Settings & environment variables
│   ├── database.py          # Database connection & session
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py          # User SQLAlchemy model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── enums.py         # UserRole enum
│   │   ├── user.py          # User Pydantic schemas
│   │   └── auth.py          # Auth schemas (Token, Login, etc.)
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── dependencies.py  # Auth dependencies (get_current_user, require_roles)
│   │   └── security.py      # JWT, password hashing utilities
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication routes
│   │   ├── superadmin.py    # Superadmin routes
│   │   ├── admin.py         # Admin routes
│   │   └── user.py          # User self-management routes
│   └── utils/
│       ├── __init__.py
│       └── email.py         # Email sending utility
```

---

## 🔒 Security Considerations

1. **Password Security:**
   - Passwords hashed with bcrypt
   - Never stored in plain text
   - Minimum 8 characters required

2. **JWT Security:**
   - Secret key stored in environment variables
   - Token expiration (30 minutes default)
   - Role-based access control

3. **Email Security:**
   - Credentials sent via email (consider encryption in production)
   - Users should change password on first login (optional enhancement)

4. **Input Validation:**
   - Pydantic schemas for request validation
   - Email format validation
   - Role validation

---

## ✅ Implementation Checklist

- [ ] Database models (User)
- [ ] Enums (UserRole)
- [ ] Pydantic schemas
- [ ] JWT authentication utilities
- [ ] Password hashing utilities
- [ ] Role-based authorization dependencies
- [ ] Email sending utility
- [ ] Authentication routes
- [ ] Superadmin routes (CRUD for Admins)
- [ ] Admin routes (CRUD for Teaching/Publishing/Small Groups)
- [ ] User self-management routes
- [ ] Hard-coded Superadmin initialization
- [ ] Database migrations (Alembic)
- [ ] Configuration management
- [ ] Main FastAPI app setup

---

## 🚀 Next Steps

1. Implement database models
2. Create authentication system
3. Implement role-based authorization
4. Create API routes
5. Add email functionality
6. Initialize Superadmin on startup
7. Test all endpoints

---

## 🔍 Code Analysis & Security Audit

### 🔴 CRITICAL SECURITY ISSUES

#### 1. **Hard-coded Credentials (CRITICAL)**
**Location:** `app/routes/auth.py:31`, `app/main.py:30-49`

**Issue:** Superadmin credentials are hard-coded in multiple places:
- Email: `superadmin@gmail.com`
- Password: `superadmin@123`

**Risk:** 
- Anyone with access to the codebase can gain superadmin access
- Credentials are exposed in version control
- Cannot be changed without code deployment

**Fix:** Move to environment variables in `app/config.py`:
```python
superadmin_email: str
superadmin_password: str
```

#### 2. **CORS Configuration Allows All Origins (HIGH)**
**Location:** `app/main.py:70-76`

**Issue:** `allow_origins=["*"]` allows ANY origin to access the API.

**Risk:** CSRF attacks, unauthorized API access.

**Fix:** Whitelist specific origins:
```python
allow_origins=[
    "https://yourdomain.com",
    "http://localhost:3000"  # Only for development
]
```

#### 3. **Plain Text Passwords Sent via Email (HIGH)**
**Location:** `app/routes/admin.py:23`, `app/routes/superadmin.py:23`

**Issue:** Passwords are sent in plain text via email.

**Risk:** Email interception exposes passwords.

**Fix:** Send temporary password with forced reset on first login.

#### 4. **No Rate Limiting (MEDIUM-HIGH)**
**Risk:** Brute force attacks on login endpoints, OTP spam.

**Fix:** Implement rate limiting using `slowapi` or `fastapi-limiter`.

#### 5. **Weak OTP Generation (MEDIUM)**
**Location:** `app/auth/security.py:78-81`

**Issue:** Uses `random.randint()` which is not cryptographically secure.

**Fix:**
```python
import secrets
def generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)
```

#### 6. **No Password Strength Validation (MEDIUM)**
**Location:** `app/schemas/user.py`

**Issue:** No minimum password requirements enforced.

**Fix:** Add Pydantic validators for password strength.

#### 7. **Debug Print Statements (LOW-MEDIUM)**
**Location:** `app/config.py:9-15`, `app/utils/email.py:36-65`

**Issue:** Debug prints expose OTP codes and sensitive information.

**Fix:** Use proper logging instead of print statements.

### 🟡 CODE QUALITY ISSUES

#### 8. **Deprecated `datetime.utcnow()` Usage**
**Location:** Multiple files

**Issue:** `datetime.utcnow()` is deprecated in Python 3.12+

**Fix:** Replace with `datetime.now(timezone.utc)`

#### 9. **Inconsistent Error Handling**
**Issue:** Some endpoints return generic errors, missing error logging.

**Fix:** Implement centralized error handling and consistent error responses.

#### 10. **Missing Input Validation**
**Issue:** No comprehensive validation beyond basic Pydantic checks.

**Fix:** Add custom validators for business rules.

#### 11. **Fragile OTP Extraction Logic**
**Location:** `app/utils/email.py:49-64`

**Issue:** String parsing breaks if message format changes.

**Fix:** Pass OTP as separate parameter or use structured templates.

#### 12. **Database Transaction Handling**
**Issue:** No explicit transaction rollback on errors.

**Fix:** Add try/except blocks with rollback.

#### 13. **Code Duplication**
**Location:** `app/routes/admin.py`

**Issue:** Teaching, Publishing, and Small Groups endpoints are nearly identical.

**Fix:** Create generic CRUD functions to reduce duplication.

### 📋 PRIORITY FIX LIST

#### Immediate (Before Production)
1. ✅ Remove hard-coded credentials → Use environment variables
2. ✅ Fix CORS configuration → Whitelist specific origins
3. ✅ Implement rate limiting → Protect authentication endpoints
4. ✅ Use secure OTP generation → Replace `random` with `secrets`
5. ✅ Remove debug print statements → Use proper logging
6. ✅ Add password strength validation → Enforce minimum requirements

#### High Priority
7. ✅ Fix deprecated `datetime.utcnow()` → Use `datetime.now(timezone.utc)`
8. ✅ Improve email security → Don't send plain text passwords
9. ✅ Add comprehensive error handling → Centralized error management
10. ✅ Add input validation → Strengthen Pydantic validators

#### Medium Priority
11. ✅ Reduce code duplication → Refactor admin routes
12. ✅ Improve transaction handling → Add rollback logic
13. ✅ Add logging infrastructure → Structured logging
14. ✅ Add unit tests → Test critical functions

### 📊 Security Score: 4/10

**Breakdown:**
- Authentication: 6/10 (Good JWT, but hard-coded creds)
- Authorization: 7/10 (Good RBAC)
- Input Validation: 5/10 (Basic validation)
- Data Protection: 4/10 (Plain text passwords in emails)
- Error Handling: 5/10 (Inconsistent)
- Rate Limiting: 0/10 (Not implemented)
- Logging: 3/10 (Debug prints, no structured logging)

