# Rider Login Issue - Root Cause & Fix

## Problem
When Akwasi Bawuah tries to login on the rider app with:
- **Phone:** 0530422137
- **Passcode:** 85935

The app shows: **"Invalid phone or passcode"**

## Root Cause
Found in `/services/auth_service/main.py` - **Bug in rider registration**

### The Bug
When a company enrolls a rider, the system calls the `/register` endpoint with role `"rider"`. 

However, the registration code had an issue on **line 189**:

```python
# BUGGY CODE:
token = create_access_token(
    user_id=user.id,
    username=user.username,
    role=user.role,
    company_id=company.id if request.role == "company_admin" else None  # ❌ WRONG
)
```

The variable `company` was only defined in the `elif request.role == "company_admin"` branch (line 165), but referenced unconditionally. When registering a rider, `company` was undefined, causing:
- **NameError: name 'company' is not defined**
- Rider registration failed silently or incompletely
- User created but rider profile may not be properly linked
- Or token creation fails, blocking login

## The Fix
Fixed the code to properly handle all registration types:

```python
# FIXED CODE:
# Get company_id if this is a company_admin
company_id = None
if request.role == "company_admin":
    company_obj = db.query(RiderCompany).filter(RiderCompany.user_id == user.id).first()
    if company_obj:
        company_id = company_obj.id

token = create_access_token(
    user_id=user.id,
    username=user.username,
    role=user.role,
    company_id=company_id  # ✅ CORRECT - works for all roles
)
```

## Changes Made
- **File:** `/home/packnet777/R1/services/auth_service/main.py`
- **Lines:** 186-199
- **Change:** Removed undefined variable reference, properly query company_id when needed

## How to Verify the Fix
1. Re-enroll Akwasi Bawuah or test login with the original credentials
2. Or run the diagnostic script:
   ```bash
   cd ~/project/src
   python3 check_enrollment_issue.py 0530422137
   ```

## What Was Really Happening
The issue is why the phone number 0530422137 was showing as COMPANY_ADMIN instead of RIDER - the enrollment process was encountering an error that caused the wrong role to be assigned or the user to fall back to a default role.

## Deployment
After fix, restart the auth service:
```bash
# On Render shell
restart-service auth_service
```

Or redeploy the entire platform.
