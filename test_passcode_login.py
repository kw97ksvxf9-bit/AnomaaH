#!/usr/bin/env python3
"""
Test passcode login directly to identify the exact issue.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shared.database import get_db
from shared.models import User, Rider, UserRole
from shared.auth import verify_password, hash_password

def test_passcode_login(phone, passcode):
    """Test the exact login logic."""
    db = next(get_db())
    try:
        print(f"\n{'='*60}")
        print(f"Testing Passcode Login")
        print(f"{'='*60}")
        print(f"Phone: {phone}")
        print(f"Passcode: {passcode}\n")
        
        # Step 1: Find user by phone
        user = db.query(User).filter(User.phone == phone).first()
        
        if not user:
            print(f"❌ Step 1: No user found with phone: {phone}")
            return False
        
        print(f"✅ Step 1: User found")
        print(f"   Username: {user.username}")
        print(f"   Role: {user.role}")
        
        # Step 2: Check role
        if user.role != UserRole.RIDER:
            print(f"\n❌ Step 2: User role is {user.role}, not RIDER")
            return False
        
        print(f"✅ Step 2: User is a RIDER\n")
        
        # Step 3: Verify password/passcode
        print(f"Step 3: Verifying passcode...")
        print(f"   Provided passcode: '{passcode}'")
        print(f"   Password hash: {user.password_hash[:30]}...")
        
        is_valid = verify_password(passcode, user.password_hash)
        print(f"   Verification result: {is_valid}\n")
        
        if not is_valid:
            print(f"❌ Passcode is INVALID!")
            print(f"\nDEBUGGING INFO:")
            print(f"   - Passcode: '{passcode}'")
            print(f"   - Length: {len(passcode)} chars")
            print(f"   - Is digit: {passcode.isdigit()}")
            print(f"   - Hash: {user.password_hash}")
            
            # Try to re-hash the passcode and compare
            test_hash = hash_password(passcode)
            print(f"   - Test hash of passcode: {test_hash}")
            print(f"   - Hash matches: {test_hash == user.password_hash}")
            
            return False
        
        print(f"✅ Step 3: Passcode is VALID\n")
        
        # Step 4: Check status
        if user.is_banned:
            print(f"❌ Step 4: Account is BANNED")
            return False
        if user.is_suspended:
            print(f"❌ Step 4: Account is SUSPENDED")
            return False
        if not user.is_active:
            print(f"❌ Step 4: Account is NOT ACTIVE")
            return False
        
        print(f"✅ Step 4: Account is active and not banned/suspended\n")
        
        # Step 5: Check rider profile
        rider = db.query(Rider).filter(Rider.user_id == user.id).first()
        if not rider:
            print(f"❌ Step 5: No rider profile found")
            return False
        
        print(f"✅ Step 5: Rider profile found")
        print(f"   Rider ID: {rider.id}")
        print(f"   Company ID: {rider.company_id}\n")
        
        print(f"✅ ALL CHECKS PASSED - Login should work!\n")
        return True
        
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_passcode_login.py <phone> <passcode>")
        print("Example: python test_passcode_login.py 0501225489 12345")
        sys.exit(1)
    
    phone = sys.argv[1].strip()
    passcode = sys.argv[2].strip()
    success = test_passcode_login(phone, passcode)
    sys.exit(0 if success else 1)
