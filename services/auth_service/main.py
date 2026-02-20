"""
Authentication Service - JWT-based authentication with PostgreSQL
Handles user registration, login, and token management
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import logging

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db, engine, Base
from shared.models import User, Merchant, RiderCompany, Rider, UserRole, Message
from shared.auth import (
    hash_password, verify_password, create_access_token, 
    decode_token, get_current_user, Token, TokenPayload
)
from shared.security import sanitize_string, validate_email, validate_phone, setup_security_middleware, check_rate_limit, get_client_ip, auth_limiter
from fastapi import Request

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Authentication Service")

# Setup security middleware
setup_security_middleware(app)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Pydantic Models ====================

class RegisterRequest(BaseModel):
    username: str
    email: str
    role: str  # "merchant", "company_admin", "rider"
    password: str
    phone: str
    
    # Additional fields for merchants and companies
    store_name: Optional[str] = None
    momo_number: Optional[str] = None
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    
    # Additional fields for riders
    bike_id: Optional[str] = None
    company_id: Optional[str] = None  # link rider to a company
    license_doc: Optional[str] = None  # base64 encoded ID/license
    full_name: Optional[str] = None
    
    @validator('username')
    def username_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return sanitize_string(v)
    
    @validator('email')
    def email_valid(cls, v):
        if not validate_email(v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('password')
    def password_valid(cls, v, values):
        # Riders use 5-digit numeric passcodes, other roles need 8+ chars
        role = values.get('role', '')
        if role == 'rider':
            if len(v) < 5:
                raise ValueError('Rider passcode must be exactly 5 digits')
            if not v.isdigit():
                raise ValueError('Rider passcode must be numbers only')
        else:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters')
        return v
    
    @validator('phone')
    def phone_valid(cls, v):
        if not validate_phone(v):
            raise ValueError('Invalid phone format')
        return v

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

# ==================== Health Check ====================

@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth"}

# ==================== Registration ====================

@app.post("/register", response_model=Token)
async def register(request: RegisterRequest, db: Session = Depends(get_db), req: Request = None):
    """Register a new user."""
    
    # Apply rate limiting (5 requests per minute for auth endpoints)
    if req:
        client_id = get_client_ip(req)
        if not check_rate_limit(client_id, auth_limiter):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many registration attempts. Please try again later."
            )
    
    # Validate role
    if request.role not in ["merchant", "company_admin", "rider"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'merchant', 'company_admin', or 'rider'"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    try:
        # Create user
        user = User(
            username=request.username,
            email=request.email,
            password_hash=hash_password(request.password),
            phone=request.phone,
            role=UserRole[request.role.upper()],
            is_active=True
        )
        db.add(user)
        db.flush()  # Get the user ID
        
        # Create role-specific profile
        if request.role == "merchant":
            merchant = Merchant(
                user_id=user.id,
                store_name=request.store_name or request.username,
                momo_number=request.momo_number,
                status="pending"
            )
            db.add(merchant)
        
        elif request.role == "company_admin":
            company = RiderCompany(
                user_id=user.id,
                company_name=request.company_name or request.username,
                contact_person=request.contact_person,
                contact_phone=request.phone,
                status="pending"
            )
            db.add(company)
        
        elif request.role == "rider":
            rider = Rider(
                user_id=user.id,
                company_id=request.company_id,
                bike_id=request.bike_id,
                license_doc=request.license_doc,
                full_name=request.full_name,
            )
            db.add(rider)
        
        db.commit()
        
        logger.info(f"User registered: {user.username} ({request.role})")
        
        # Create token
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
            company_id=company_id
        )
        
        return Token(
            access_token=token,
            user_id=user.id,
            role=user.role
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

# ==================== Login ====================

@app.post("/login", response_model=Token)
async def login(request: LoginRequest, db: Session = Depends(get_db), req: Request = None):
    """Login and get JWT token."""
    
    # Apply rate limiting (5 requests per minute for auth endpoints)
    if req:
        client_id = get_client_ip(req)
        if not check_rate_limit(client_id, auth_limiter):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
    
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is banned"
        )
    
    if user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended"
        )
    
    # Get company_id if user has a company
    company_id = None
    if user.role == UserRole.COMPANY_ADMIN and user.company:
        company_id = user.company.id
    
    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
        company_id=company_id
    )
    
    logger.info(f"Login successful: {user.username}")
    
    return Token(
        access_token=token,
        user_id=user.id,
        role=user.role
    )

# ==================== User Management ====================

@app.get("/me")
async def get_current_user_info(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    user = db.query(User).filter(User.id == current_user.user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    result = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at
    }

    # Include merchant profile fields if user is a merchant
    if user.role == "merchant":
        merchant = db.query(Merchant).filter(Merchant.user_id == user.id).first()
        if merchant:
            result["store_name"] = merchant.store_name
            result["store_address"] = merchant.store_address
            result["momo_number"] = merchant.momo_number
            result["merchant_status"] = merchant.status

    return result

@app.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    user = db.query(User).filter(User.id == current_user.user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify old password
    if not verify_password(request.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    db.commit()
    
    logger.info(f"Password changed: {user.username}")
    
    return {"message": "Password changed successfully"}

@app.post("/logout")
async def logout(current_user: TokenPayload = Depends(get_current_user)):
    """Logout (invalidate token on client side)."""
    logger.info(f"Logout: {current_user.username}")
    return {"message": "Logged out successfully"}

# ==================== Admin Functions ====================

@app.get("/users")
async def list_users(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users (superadmin only)."""
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmins can view all users"
        )
    
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at
        }
        for u in users
    ]

@app.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Suspend a user account.
    - superadmin can suspend company_admin and merchant only (NOT riders)
    - company_admin can suspend their own riders
    """
    if current_user.role not in ("superadmin", "company_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to suspend users"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # superadmin can only suspend company_admin and merchant, NOT riders
    if current_user.role == "superadmin":
        if user.role not in ("company_admin", "merchant"):
            raise HTTPException(status_code=403, detail="Superadmin can only suspend companies and merchants, not individual riders")
    
    # company_admin can only suspend riders in their company
    if current_user.role == "company_admin":
        rider = db.query(Rider).filter(Rider.user_id == user_id).first()
        if not rider or rider.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Can only suspend your own riders")
    
    user.is_suspended = True
    db.commit()
    
    logger.info(f"User suspended: {user.username} by {current_user.username}")
    
    return {"message": f"User {user.username} suspended"}

@app.post("/users/{user_id}/ban")
async def ban_user(
    user_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ban a user account.
    - superadmin can ban company_admin and merchant only (NOT riders)
    - company_admin can ban their own riders
    """
    if current_user.role not in ("superadmin", "company_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to ban users"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # superadmin can only ban company_admin and merchant, NOT riders
    if current_user.role == "superadmin":
        if user.role not in ("company_admin", "merchant"):
            raise HTTPException(status_code=403, detail="Superadmin can only ban companies and merchants, not individual riders")
    
    # company_admin can only ban riders in their company
    if current_user.role == "company_admin":
        rider = db.query(Rider).filter(Rider.user_id == user_id).first()
        if not rider or rider.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Can only ban your own riders")
    
    user.is_banned = True
    db.commit()
    
    logger.info(f"User banned: {user.username} by {current_user.username}")
    
    return {"message": f"User {user.username} banned"}

# ==================== OTP-Based Phone Login (for Rider App) ====================

# In-memory OTP store for demo (in production, use Redis + real SMS)
_otp_store: dict = {}
DEMO_OTP = "123456"

class PhoneLoginRequest(BaseModel):
    phone: str

class OtpVerifyRequest(BaseModel):
    phone: str
    otp: str

@app.post("/auth/login")
async def phone_login(request: PhoneLoginRequest, db: Session = Depends(get_db)):
    """Send OTP to phone number (demo: always uses 123456)."""
    phone = request.phone.strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number required")

    # Store OTP (demo mode: always 123456)
    _otp_store[phone] = DEMO_OTP
    logger.info(f"OTP sent to {phone}: {DEMO_OTP} (demo mode)")

    return {
        "success": True,
        "message": f"OTP sent to {phone}. For demo use: {DEMO_OTP}"
    }

@app.post("/auth/verify-otp")
async def verify_otp(request: OtpVerifyRequest, db: Session = Depends(get_db)):
    """Verify OTP and return JWT token + rider profile."""
    phone = request.phone.strip()
    otp = request.otp.strip()

    # Demo mode: accept 123456 for any phone
    stored_otp = _otp_store.get(phone, DEMO_OTP)
    if otp != stored_otp and otp != DEMO_OTP:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    # Find or create rider user by phone
    user = db.query(User).filter(User.phone == phone).first()

    if not user:
        # Auto-register rider on first OTP verify
        user = User(
            username=f"rider_{phone[-4:]}",
            email=f"rider_{phone[-4:]}@delivery.local",
            password_hash=hash_password(DEMO_OTP),
            phone=phone,
            role=UserRole.RIDER,
            is_active=True
        )
        db.add(user)
        db.flush()

        rider = Rider(
            user_id=user.id,
            company_id=None
        )
        db.add(rider)
        db.commit()
        logger.info(f"Auto-registered rider for phone {phone}")

    # Get rider profile
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()

    # Get company_id
    company_id = None
    if user.role == UserRole.COMPANY_ADMIN and user.company:
        company_id = user.company.id
    elif rider and rider.company_id:
        company_id = rider.company_id

    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        company_id=company_id
    )

    # Clean up OTP
    _otp_store.pop(phone, None)

    rider_data = None
    if rider:
        rider_data = {
            "id": rider.id,
            "name": user.username,
            "phone": user.phone,
            "email": user.email,
            "companyId": rider.company_id,
            "rating": rider.avg_rating,
            "totalDeliveries": rider.completed_orders,
            "totalEarnings": rider.total_earnings,
            "status": rider.status.value if hasattr(rider.status, 'value') else str(rider.status),
            "verified": True
        }

    return {
        "success": True,
        "message": "Login successful",
        "accessToken": token,
        "data": rider_data,
        "rider": rider_data
    }

@app.post("/auth/logout")
async def auth_logout(current_user: TokenPayload = Depends(get_current_user)):
    """Logout (rider app)."""
    logger.info(f"Rider logout: {current_user.username}")
    return {"success": True, "message": "Logged out successfully"}

@app.get("/auth/me")
async def auth_me(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current rider info (rider app)."""
    user = db.query(User).filter(User.id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    rider_data = None
    if rider:
        rider_data = {
            "id": rider.id,
            "name": user.username,
            "phone": user.phone,
            "email": user.email,
            "companyId": rider.company_id,
            "rating": rider.avg_rating,
            "totalDeliveries": rider.completed_orders,
            "totalEarnings": rider.total_earnings,
            "status": rider.status.value if hasattr(rider.status, 'value') else str(rider.status),
            "verified": True
        }

    return {
        "success": True,
        "message": "User found",
        "data": rider_data,
        "rider": rider_data
    }

# ==================== Token Endpoint (for Admin UI login) ====================

@app.post("/token")
async def token_login(request: LoginRequest, db: Session = Depends(get_db)):
    """Username/password login that returns access_token (admin UI compatible)."""
    user = db.query(User).filter(User.username == request.username).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account banned")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Account suspended")

    company_id = None
    if user.role == UserRole.COMPANY_ADMIN and user.company:
        company_id = user.company.id

    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        company_id=company_id
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role)
    }


# ==================== Reactivate User ====================

@app.post("/users/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reactivate a suspended/banned user (superadmin or company_admin for their riders)."""
    if current_user.role not in ("superadmin", "company_admin"):
        raise HTTPException(status_code=403, detail="Not authorised")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.role == "company_admin":
        rider = db.query(Rider).filter(Rider.user_id == user_id).first()
        if not rider or rider.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Can only reactivate your own riders")

    user.is_suspended = False
    user.is_banned = False
    user.is_active = True
    db.commit()
    logger.info(f"User reactivated: {user.username} by {current_user.username}")
    return {"message": f"User {user.username} reactivated"}


# ==================== Company Riders (filtered by company) ====================

@app.get("/company/riders")
async def get_company_riders(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all riders belonging to this company admin's company."""
    if current_user.role != "company_admin":
        raise HTTPException(status_code=403, detail="Only company admins")

    company = db.query(RiderCompany).filter(RiderCompany.user_id == current_user.user_id).first()
    if not company:
        return []

    riders = db.query(Rider).filter(Rider.company_id == company.id).all()
    result = []
    for r in riders:
        u = db.query(User).filter(User.id == r.user_id).first()
        result.append({
            "rider_id": r.id,
            "user_id": r.user_id,
            "username": u.username if u else "",
            "full_name": r.full_name or (u.username if u else ""),
            "email": u.email if u else "",
            "phone": u.phone if u else "",
            "bike_id": r.bike_id or "",
            "has_license": bool(r.license_doc),
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "is_active": u.is_active if u else False,
            "is_suspended": u.is_suspended if u else False,
            "is_banned": u.is_banned if u else False,
            "completed_orders": r.completed_orders,
            "avg_rating": r.avg_rating,
            "total_earnings": r.total_earnings,
            "current_lat": r.current_lat,
            "current_lng": r.current_lng,
            "created_at": str(r.created_at) if r.created_at else None,
        })
    return result


# ==================== Commission Management ====================

@app.get("/company/commission")
async def get_commission(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get company commission percentage."""
    company = db.query(RiderCompany).filter(RiderCompany.user_id == current_user.user_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"commission_pct": company.commission_pct, "company_id": company.id, "company_name": company.company_name}


@app.post("/company/commission")
async def update_commission(
    payload: dict,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update company commission percentage."""
    if current_user.role != "company_admin":
        raise HTTPException(status_code=403, detail="Only company admins")
    company = db.query(RiderCompany).filter(RiderCompany.user_id == current_user.user_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    pct = payload.get("commission_pct")
    if pct is None or not (0 <= float(pct) <= 100):
        raise HTTPException(status_code=400, detail="commission_pct must be 0-100")
    company.commission_pct = float(pct)
    db.commit()
    logger.info(f"Commission updated to {pct}% for {company.company_name} by {current_user.username}")
    return {"ok": True, "commission_pct": company.commission_pct}


# ==================== In-App Messaging ====================

@app.post("/company/messages/send")
async def send_message(
    payload: dict,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Company admin sends message to a rider."""
    if current_user.role != "company_admin":
        raise HTTPException(status_code=403, detail="Only company admins")

    company = db.query(RiderCompany).filter(RiderCompany.user_id == current_user.user_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    rider_user_id = payload.get("rider_user_id")
    content = payload.get("message", "").strip()
    is_alert = payload.get("is_alert", False)

    if not rider_user_id or not content:
        raise HTTPException(status_code=400, detail="rider_user_id and message required")

    # Verify rider belongs to company
    rider = db.query(Rider).filter(Rider.user_id == rider_user_id, Rider.company_id == company.id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found in your company")

    msg = Message(
        company_id=company.id,
        rider_id=rider.id,
        sender="admin",
        content=content,
        is_alert=is_alert,
    )
    db.add(msg)
    db.commit()
    logger.info(f"Message sent to rider {rider_user_id} by {current_user.username}")
    return {"ok": True, "message_id": msg.id}


@app.get("/company/messages/{rider_user_id}")
async def get_messages(
    rider_user_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get message history between company and a rider."""
    company = db.query(RiderCompany).filter(RiderCompany.user_id == current_user.user_id).first()
    if not company:
        return []

    rider = db.query(Rider).filter(Rider.user_id == rider_user_id, Rider.company_id == company.id).first()
    if not rider:
        return []

    msgs = db.query(Message).filter(
        Message.company_id == company.id,
        Message.rider_id == rider.id,
    ).order_by(Message.created_at.asc()).all()

    return [
        {
            "id": m.id,
            "sender": m.sender,
            "content": m.content,
            "is_alert": m.is_alert,
            "created_at": str(m.created_at) if m.created_at else None,
        }
        for m in msgs
    ]


# ==================== Rider Passcode Login (Phone + 5-digit code) ====================

class PasscodeLoginRequest(BaseModel):
    phone: str
    passcode: str

class ChangePasscodeRequest(BaseModel):
    new_passcode: str

@app.post("/rider/passcode-login")
async def rider_passcode_login(request: PasscodeLoginRequest, db: Session = Depends(get_db)):
    """Login rider with phone number + 5-digit passcode (assigned by company)."""
    phone = request.phone.strip()
    passcode = request.passcode.strip()

    if not phone or not passcode:
        raise HTTPException(status_code=400, detail="Phone and passcode required")

    # Find rider by phone (phone is stored on User model)
    user = db.query(User).filter(User.phone == phone, User.role == UserRole.RIDER).first()
    if not user:
        raise HTTPException(status_code=401, detail="No rider account found for this phone number")

    if not verify_password(passcode, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid passcode")

    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account banned. Contact your company admin.")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Account suspended. Contact your company admin.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")

    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    company_id = rider.company_id if rider else None

    # Get company info
    company_name = None
    if company_id:
        company = db.query(RiderCompany).filter(RiderCompany.id == company_id).first()
        if company:
            company_name = company.company_name

    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        company_id=company_id
    )

    rider_data = None
    if rider:
        rider_data = {
            "id": rider.id,
            "name": rider.full_name or user.username,
            "phone": user.phone,
            "email": user.email,
            "companyId": rider.company_id,
            "companyName": company_name,
            "bikeId": rider.bike_id,
            "rating": rider.avg_rating,
            "totalDeliveries": rider.completed_orders,
            "totalEarnings": rider.total_earnings,
            "status": rider.status.value if hasattr(rider.status, 'value') else str(rider.status),
            "verified": True,
            "fullName": rider.full_name,
        }

    logger.info(f"Rider passcode login: {user.username} ({phone})")

    return {
        "success": True,
        "message": "Login successful",
        "accessToken": token,
        "data": rider_data,
        "rider": rider_data
    }


@app.post("/rider/change-passcode")
async def rider_change_passcode(
    request: ChangePasscodeRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rider changes their own 5-digit passcode. Company admin gets notified."""
    new_passcode = request.new_passcode.strip()

    if not new_passcode or len(new_passcode) < 5 or len(new_passcode) > 5:
        raise HTTPException(status_code=400, detail="Passcode must be exactly 5 digits")
    if not new_passcode.isdigit():
        raise HTTPException(status_code=400, detail="Passcode must be numeric (5 digits)")

    user = db.query(User).filter(User.id == current_user.user_id).first()
    if not user or user.role != UserRole.RIDER:
        raise HTTPException(status_code=403, detail="Only riders can change passcode")

    # Update passcode
    user.password_hash = hash_password(new_passcode)
    db.flush()

    # Notify company admin via messaging system
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if rider and rider.company_id:
        notification_msg = Message(
            company_id=rider.company_id,
            rider_id=rider.id,
            sender="system",
            content=f"🔑 {rider.full_name or user.username} has updated their login passcode.",
            is_alert=True,
        )
        db.add(notification_msg)

    db.commit()
    logger.info(f"Rider passcode changed: {user.username}")

    return {"success": True, "message": "Passcode updated successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8600)
