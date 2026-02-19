"""
Alembic configuration and initialization script.
Run: alembic init alembic
Then configure the migration environment.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import engine_from_config, pool
from alembic import context

# Import models
from shared.database import Base
from shared.models import (
    User, Merchant, RiderCompany, Rider,
    Order, OrderTracking, Payment, Transaction, Payout,
    RiderDocument, RiderReview, Message
)

# Get database URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/delivery"
)

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Set target_metadata for auto migrations
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
