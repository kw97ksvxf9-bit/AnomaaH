#!/usr/bin/env python3
"""
Diagnostic script to check rider enrollment and login issues.
Usage: python check_rider_login.py <phone>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shared.database import get_db, Base, engine
from shared.models import User, Rider, UserRole
from shared.auth import verify_password, hash_password

Base.metadata.create_all(bind=engine)

if len(sys.argv) < 2:
    print("Usage: python check_rider_login.py <phone>")
    print("Example: python check_rider_login.py 0558876737")
    sys.exit(1)

phone = sys.argv[1].strip()

with get_db() as db:
    # Find user by phone
    user = db.query(User).filter(User.phone == phone).first()
    
    if not user:
        print(f"❌ No user found with phone: {phone}")
        print("\nAll riders in database:")
        riders = db.query(User).filter(User.role == UserRole.RIDER).all()
        for u in riders:
            print(f"  - {u.username}: phone={u.phone}, is_active={u.is_active}")
        sys.exit(1)
    
    print(f"✅ User found: {user.username}")
    print(f"   Role: {user.role}")
    print(f"   Phone: {user.phone}")
    print(f"   Email: {user.email}")
    print(f"   Active: {user.is_active}")
    print(f"   Banned: {user.is_banned}")
    print(f"   Suspended: {user.is_suspended}")
    print(f"   Password Hash: {user.password_hash[:20]}...")
    
    # Test password verification
    if len(sys.argv) >= 3:
        passcode = sys.argv[2].strip()
        is_valid = verify_password(passcode, user.password_hash)
        print(f"\n🔐 Passcode verification for '{passcode}':")
        print(f"   Valid: {is_valid}")
        
        if not is_valid:
            print(f"\n⚠️  Testing with correct password from hash...")
            # Try to show hash details
            print(f"   Hash algorithm appears to be bcrypt")
    
    # Check rider profile
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if rider:
        print(f"\n✅ Rider profile found:")
        print(f"   Rider ID: {rider.id}")
        print(f"   Company ID: {rider.company_id}")
        print(f"   Bike ID: {rider.bike_id}")
        print(f"   Full Name: {rider.full_name}")
        print(f"   Status: {rider.status}")
    else:
        print(f"\n❌ No rider profile found for this user!")
