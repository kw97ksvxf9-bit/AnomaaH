#!/usr/bin/env python3
"""
Reset/Set a rider's passcode directly in the database.
Use this when enrollment failed or the password was not properly saved.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shared.database import get_db
from shared.models import User, UserRole
from shared.auth import hash_password

def set_rider_passcode(phone, new_passcode):
    """Set a new passcode for a rider."""
    db = next(get_db())
    try:
        print(f"\n{'='*60}")
        print(f"Setting Rider Passcode")
        print(f"{'='*60}")
        print(f"Phone: {phone}")
        print(f"New Passcode: {new_passcode}\n")
        
        # Find user by phone
        user = db.query(User).filter(User.phone == phone).first()
        
        if not user:
            print(f"❌ No user found with phone: {phone}")
            return False
        
        print(f"✅ User found: {user.username}")
        print(f"   Current role: {user.role}")
        
        # Validate passcode
        if not isinstance(new_passcode, str):
            new_passcode = str(new_passcode)
        
        new_passcode = new_passcode.strip()
        
        if len(new_passcode) != 5:
            print(f"❌ Passcode must be exactly 5 digits, got: {len(new_passcode)}")
            return False
        
        if not new_passcode.isdigit():
            print(f"❌ Passcode must be numeric only")
            return False
        
        # Hash and set the new passcode
        old_hash = user.password_hash
        user.password_hash = hash_password(new_passcode)
        db.commit()
        
        print(f"\n✅ Passcode updated successfully!")
        print(f"   Old hash: {old_hash[:30]}...")
        print(f"   New hash: {user.password_hash[:30]}...\n")
        print(f"Rider can now login with:")
        print(f"   Phone: {user.phone}")
        print(f"   Passcode: {new_passcode}\n")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python set_rider_passcode.py <phone> <new_passcode>")
        print("Example: python set_rider_passcode.py 0530422137 85935")
        print("\nNote: Passcode must be exactly 5 digits")
        sys.exit(1)
    
    phone = sys.argv[1].strip()
    passcode = sys.argv[2].strip()
    success = set_rider_passcode(phone, passcode)
    sys.exit(0 if success else 1)
