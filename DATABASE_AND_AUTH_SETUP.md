# Database & Authentication Setup Guide

## Overview
This guide covers the new PostgreSQL database layer, SQLAlchemy ORM, JWT authentication, and security middleware integrated into the platform.

## Components

### 1. Database Layer (`shared/database.py`)
- SQLAlchemy engine and session factory
- PostgreSQL connection configuration via `DATABASE_URL` environment variable
- FastAPI dependency injection for database sessions

### 2. Database Models (`shared/models.py`)
Complete SQLAlchemy models for all entities:

**User Management:**
- `User` - Base user entity with roles (superadmin, company_admin, merchant, rider)
- `Merchant` - Merchant account details
- `RiderCompany` - Rider company (tenant) details
- `Rider` - Rider profile with status and earnings

**Order Management:**
- `Order` - Order entity with status state machine (PENDING → ASSIGNED → PICKED_UP → IN_TRANSIT → DELIVERED)
- `OrderTracking` - Tracking link and real-time location for orders

**Payment & Payouts:**
- `Payment` - Payment records with Hubtel integration
- `Transaction` - Transaction logs
- `Payout` - Payout records to riders and companies

**Documents & Reviews:**
- `RiderDocument` - Rider documents (license, insurance, ID)
- `RiderReview` - Rider ratings and reviews

**Messaging:**
- `Message` - Company-to-rider messaging and alerts

### 3. Authentication (`shared/auth.py`)
JWT-based authentication with:
- Password hashing using bcrypt
- Token creation and validation
- Role-based access control (RBAC)
- User dependency injection for FastAPI

**Key Functions:**
- `hash_password()` - Securely hash passwords
- `create_access_token()` - Generate JWT tokens
- `decode_token()` - Validate and decode tokens
- `get_current_user()` - FastAPI dependency for protected routes
- `require_role()` - Decorator for role-based access
- `require_company()` - Decorator for company-specific access

### 4. Security Middleware (`shared/security.py`)
- Input sanitization and validation
- Security headers (CSP, X-Frame-Options, HSTS, etc.)
- Email, phone, URL, and coordinate validation
- Rate limiting setup (using slowapi)
- CORS configuration

## Database Setup

### 1. Install Dependencies
```bash
pip install -r requirements-db.txt
```

### 2. Initialize Database
```bash
# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/delivery"

# Create tables
bash init_db.sh
```

### 3. Connect Services to Database
Update each microservice to use the new database:

```python
# In your FastAPI service main.py
from shared.database import get_db, engine, Base
from shared.models import Order, Payment, Merchant, Rider
from shared.auth import get_current_user, require_role
from shared.security import setup_security_middleware

app = FastAPI()

# Setup security middleware
setup_security_middleware(app)

# Create tables (run once)
Base.metadata.create_all(bind=engine)

# Protected endpoint example
@app.get("/orders")
async def get_orders(
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    if current_user.role not in ["company_admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    orders = db.query(Order).filter(Order.company_id == current_user.company_id).all()
    return orders
```

## JWT Token Usage

### 1. Login (Issue Token)
```python
@app.post("/auth/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
        company_id=user.company.id if user.company else None
    )
    
    return Token(access_token=token, user_id=user.id, role=user.role)
```

### 2. Use Token in Requests
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/orders
```

## Role-Based Access Control

### Available Roles:
- `superadmin` - Full system access
- `company_admin` - Manage own company
- `merchant` - Place orders
- `rider` - Accept and complete orders

### Usage in Endpoints:
```python
@app.get("/admin/merchants")
async def list_merchants(
    current_user: TokenPayload = Depends(require_role("superadmin"))
):
    # Only superadmins can access
    pass

@app.get("/company/riders")
async def company_riders(
    current_user: TokenPayload = Depends(require_role("company_admin"))
):
    # Only company admins can access
    pass
```

## Security Best Practices

1. **Input Validation**
   ```python
   from shared.security import sanitize_string, validate_email, validate_phone
   
   username = sanitize_string(request.username)
   if not validate_email(request.email):
       raise ValidationError("Invalid email")
   ```

2. **Security Headers** - Automatically added by middleware
3. **Rate Limiting** - Apply per-endpoint:
   ```python
   @app.post("/auth/login")
   @limiter.limit("5/minute")
   async def login(request: Request, ...):
       pass
   ```

4. **HTTPS/TLS** - Use in production
5. **Environment Variables** - Never hardcode secrets

## Migration Management

### Using Alembic (Future)
```bash
# Initialize Alembic (one time)
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing the Database Layer

```python
# Test database connection
python3 -c "
from shared.database import engine, SessionLocal
from shared.models import User

session = SessionLocal()
users = session.query(User).all()
print(f'Total users: {len(users)}')
session.close()
"
```

## Next Steps

1. Update all microservices to use the new database models
2. Implement login endpoints in auth_service
3. Migrate in-memory data to PostgreSQL
4. Add comprehensive unit tests
5. Implement WebSocket for real-time updates
