#!/usr/bin/env bash
# Initialize and run database migrations

set -euo pipefail

echo "Creating database tables..."

python3 << 'EOF'
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.database import engine, Base
from shared.models import (
    User, Merchant, RiderCompany, Rider,
    Order, OrderTracking, Payment, Transaction, Payout,
    RiderDocument, RiderReview, Message
)

# Create all tables
Base.metadata.create_all(bind=engine)
print("✓ Database tables created successfully!")
EOF

echo "Database migration complete."
