#!/usr/bin/env python3
"""
Database Initialization Script

Initializes the database tables and optionally seeds sample data.

Usage:
    python scripts/init_db.py              # Create tables only
    python scripts/init_db.py --seed       # Create tables and seed data
    python scripts/init_db.py --reset      # Drop all tables and recreate
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from app.config.settings import settings
from app.db.models import Base, Task
from app.db.session import AsyncSessionLocal, engine


async def drop_tables() -> None:
    """Drop all tables."""
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("✓ Tables dropped")


async def create_tables() -> None:
    """Create all tables."""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Tables created")


async def seed_sample_data() -> None:
    """Seed database with sample tasks."""
    print("\nSeeding sample data...")

    async with AsyncSessionLocal() as session:
        # Sample tasks
        sample_tasks = [
            Task(
                user_id=settings.MOCK_USER_ID,
                title="Research MCP specification",
                project="Deep Dive Coding",
                priority=4,
                energy="deep",
                time_estimate="2hr",
                notes="Focus on tool registration and response formats",
                completed=False,
            ),
            Task(
                user_id=settings.MOCK_USER_ID,
                title="Update LinkedIn profile",
                project="Personal",
                priority=2,
                energy="light",
                time_estimate="30min",
                completed=False,
            ),
            Task(
                user_id=settings.MOCK_USER_ID,
                title="Order sublimation printer",
                project="Custom Cult",
                priority=5,
                energy="medium",
                time_estimate="1hr",
                notes="Research options: Epson F570 vs Sawgrass SG1000",
                completed=False,
            ),
            Task(
                user_id=settings.MOCK_USER_ID,
                title="Write unit tests for TaskService",
                project="Deep Dive Coding",
                priority=4,
                energy="deep",
                time_estimate="3hr",
                completed=True,
            ),
            Task(
                user_id=settings.MOCK_USER_ID,
                title="Schedule dentist appointment",
                project="Personal",
                priority=3,
                energy="light",
                time_estimate="15min",
                completed=False,
            ),
        ]

        # Add tasks to session
        for task in sample_tasks:
            session.add(task)

        # Commit changes
        await session.commit()

        print(f"✓ Seeded {len(sample_tasks)} sample tasks")


async def verify_database() -> None:
    """Verify database connection and table creation."""
    print("\nVerifying database...")

    async with AsyncSessionLocal() as session:
        # Test connection
        result = await session.execute(text("SELECT 1"))
        result.scalar()

        # Count tasks
        result = await session.execute(text("SELECT COUNT(*) FROM tasks"))
        count = result.scalar()

        print(f"✓ Database connection successful")
        print(f"✓ Tasks table exists ({count} tasks)")


async def main() -> None:
    """Main initialization workflow."""
    parser = argparse.ArgumentParser(description="Initialize Task Manager database")
    parser.add_argument("--seed", action="store_true", help="Seed sample data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables and recreate (WARNING: DATA LOSS)",
    )

    args = parser.parse_args()

    print("Task Manager MCP - Database Initialization")
    print("=" * 40)
    print()

    # Reset mode (drop and recreate)
    if args.reset:
        print("⚠️  RESET MODE: This will DELETE all existing data!")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

        await drop_tables()
        await create_tables()

        if args.seed:
            await seed_sample_data()

    # Normal mode (create only)
    else:
        await create_tables()

        if args.seed:
            await seed_sample_data()

    # Verify
    await verify_database()

    print("\n✓ Database initialization complete!")
    print(f"\nDatabase location: {settings.DATABASE_URL}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
