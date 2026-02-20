#!/usr/bin/env python3
"""
Seed default superadmin users for ANOMAAH platform.
Run this after deploying the database.
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

DEFAULT_SUPERADMINS = [
    {
        "username": "admin",
        "email": "admin@anomaah.com",
        "password": "AdminAnomaaH2025!",
        "phone": "+233000000000",
    },
    {
        "username": "superadmin",
        "email": "superadmin@anomaah.com",
        "password": "SuperAdminPass2025!",
        "phone": "+233000000001",
    },
    {
        "username": "support",
        "email": "support@anomaah.com",
        "password": "SupportPass2025!",
        "phone": "+233000000002",
    },
]

def seed_superadmins():
    """Seed default superadmin users."""
    db = next(get_db())
    
    created = 0
    skipped = 0
    
    for admin_data in DEFAULT_SUPERADMINS:
        # Check if user exists
        existing = db.query(User).filter(User.username == admin_data["username"]).first()
        if existing:
            print(f"⏭️  '{admin_data['username']}' already exists, skipping")
            skipped += 1
            continue
        
        # Create user
        hashed_pwd = hash_password(admin_data["password"])
        user = User(
            username=admin_data["username"],
            email=admin_data["email"],
            password_hash=hashed_pwd,
            phone=admin_data["phone"],
            role=UserRole.SUPERADMIN,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ Superadmin '{admin_data['username']}' created")
        print(f"   Email: {admin_data['email']}")
        print(f"   Password: {admin_data['password']}")
        print(f"   ID: {user.id}")
        print()
        
        created += 1
    
    print(f"\n📊 Summary: {created} created, {skipped} already exist")

if __name__ == "__main__":
    seed_superadmins()
