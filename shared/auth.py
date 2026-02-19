"""
JWT Authentication and Authorization Module
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Token Models
class TokenPayload(BaseModel):
    user_id: str
    username: str
    role: str
    company_id: Optional[str] = None
    exp: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str

# Password hashing functions
def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

# JWT Token functions
def create_access_token(
    user_id: str,
    username: str,
    role: str,
    company_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.utcnow() + expires_delta
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "company_id": company_id,
        "exp": expire
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("username")
        role = payload.get("role")
        company_id = payload.get("company_id")
        
        if not all([user_id, username, role]):
            return None
        
        return TokenPayload(
            user_id=user_id,
            username=username,
            role=role,
            company_id=company_id,
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# FastAPI security dependencies
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenPayload:
    """Validate JWT token and return user info."""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return payload

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[TokenPayload]:
    """Optional authentication - returns user if token is provided, None otherwise."""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    return payload

# Role-based access control
def require_role(*allowed_roles: str):
    """Create a dependency that requires one of the specified roles."""
    async def role_checker(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of the following roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def require_company(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """Require that the user has a company_id (is a company admin)."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a company context"
        )
    return current_user

def require_same_company(required_company_id: str):
    """Create a dependency that ensures user belongs to the required company."""
    async def company_checker(current_user: TokenPayload = Depends(require_company)) -> TokenPayload:
        if current_user.company_id != required_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company's resources"
            )
        return current_user
    return company_checker
