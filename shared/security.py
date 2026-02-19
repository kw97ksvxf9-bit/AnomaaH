"""
Security middleware for input validation, sanitization, security headers, and rate limiting
"""

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import re
from typing import Callable, Any
from collections import defaultdict
from datetime import datetime, timedelta
import time

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Custom rate limiter for endpoints without slowapi
class RateLimiter:
    """Simple in-memory rate limiter."""
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is allowed to make a request."""
        now = time.time()
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Add new request
        self.requests[client_id].append(now)
        return True

# Global rate limiters for different endpoints
public_limiter = RateLimiter(max_requests=20, window_seconds=60)  # 20 req/min
auth_limiter = RateLimiter(max_requests=5, window_seconds=60)  # 5 req/min for auth
api_limiter = RateLimiter(max_requests=100, window_seconds=60)  # 100 req/min for API

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; img-src 'self' data: https:; font-src 'self'; connect-src 'self' http: https: ws: wss:;"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input - remove dangerous characters."""
    if not isinstance(value, str):
        return value
    
    # Limit length
    value = value[:max_length]
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Remove control characters
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
    
    return value.strip()

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    # Allow international format: +233XXXXXXXXX or 0XXXXXXXXX or 233XXXXXXXXX
    pattern = r'^(?:\+?233|0)\d{9,10}$'
    return re.match(pattern, phone) is not None

def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None

def validate_coordinates(lat: float, lng: float) -> bool:
    """Validate GPS coordinates."""
    return -90 <= lat <= 90 and -180 <= lng <= 180

def setup_security_middleware(app):
    """Setup all security middleware and CORS for FastAPI app."""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    return app

def check_rate_limit(client_id: str, limiter: RateLimiter) -> bool:
    """Check if request is within rate limit."""
    return limiter.is_allowed(client_id)

def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    if request.client:
        return request.client.host
    return "unknown"
