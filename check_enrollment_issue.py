#!/usr/bin/env python3
"""
Diagnostic script to investigate rider enrollment issues.
Checks:
1. If the phone number is registered 
2. What role the user has
3. If a rider profile exists
4. Logs from enrollment attempt
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shared.database import get_db
from shared.models import User, Rider, UserRole

def check_rider_issue(phone_number):
    db = next(get_db())
    try:
        print(f"\n{'='*60}")
        print(f"Checking phone: {phone_number}")
        print(f"{'='*60}\n")
        
        # Find user by phone
        user = db.query(User).filter(User.phone == phone_number).first()
        
        if not user:
            print(f"❌ No user found with phone: {phone_number}")
            return False
        
        print(f"✅ User found:")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role}")
        print(f"   Active: {user.is_active}")
        print(f"   Banned: {user.is_banned}")
        print(f"   Suspended: {user.is_suspended}\n")
        
        # Check if this is a rider
        if user.role != UserRole.RIDER:
            print(f"❌ PROBLEM FOUND:")
            print(f"   User's role is '{user.role.value}' but should be 'rider'")
            print(f"   This is why login fails - rider app only accepts 'rider' role users!\n")
            return False
        
        # Check rider profile
        rider = db.query(Rider).filter(Rider.user_id == user.id).first()
        if not rider:
            print(f"❌ PROBLEM FOUND:")
            print(f"   User has 'rider' role but NO rider profile exists!")
            print(f"   A Rider profile must be created linking to company\n")
            return False
        
        print(f"✅ Rider profile found:")
        print(f"   Rider ID: {rider.id}")
        print(f"   Company ID: {rider.company_id}")
        print(f"   Bike ID: {rider.bike_id}")
        print(f"   Full Name: {rider.full_name}")
        print(f"   Status: {rider.status}\n")
        
        print(f"✅ ALL CHECKS PASSED - Rider should be able to login\n")
        return True
        
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_enrollment_issue.py <phone>")
        print("Example: python check_enrollment_issue.py 0530422137")
        sys.exit(1)
    
    phone = sys.argv[1].strip()
    success = check_rider_issue(phone)
    sys.exit(0 if success else 1)
