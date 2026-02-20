#!/usr/bin/env python3
"""
Create superadmin users in the database.
Usage: python create_superadmin.py <username> <password> <email>
"""

import os
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.database import get_db, engine, Base
from shared.models import User, UserRole
from shared.auth import hash_password

# Create tables on startup
Base.metadata.create_all(bind=engine)

def create_superadmin(username: str, password: str, email: str, phone: str = "+233000000000"):
    """Create a superadmin user."""
    db = next(get_db())
    
    # Check if user exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"❌ User '{username}' already exists")
        return False
    
    # Create user
    hashed_pwd = hash_password(password)
    user = User(
        username=username,
        email=email,
        password_hash=hashed_pwd,
        phone=phone,
        role=UserRole.SUPERADMIN,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"✅ Superadmin created:")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Phone: {phone}")
    print(f"   ID: {user.id}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python create_superadmin.py <username> <password> <email> [phone]")
        print("Example: python create_superadmin.py admin admin123 admin@anomaah.com +233000000000")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    email = sys.argv[3]
    phone = sys.argv[4] if len(sys.argv) > 4 else "+233000000000"
    
    create_superadmin(username, password, email, phone)
