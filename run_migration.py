import asyncio
import os
import glob
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL not set")
    exit(1)


async def run_migration():
    """Run all migration SQL files in order."""
    migration_files = sorted(glob.glob("migrations/*.sql"))

    if not migration_files:
        print("No migration files found in migrations/")
        return

    print(f"Found {len(migration_files)} migration file(s)")
    print(f"Connecting to database...")
    conn = await asyncpg.connect(database_url)

    try:
        for migration_file in migration_files:
            print(f"\n{'='*60}")
            print(f"Running migration: {migration_file}")
            print(f"{'='*60}")

            with open(migration_file, "r") as f:
                sql = f.read()

            try:
                await conn.execute(sql)
                print(f"✓ Migration {Path(migration_file).name} completed successfully!")
            except Exception as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg:
                    print(f"⚠ Migration {Path(migration_file).name}: Some objects already exist (skipped)")
                else:
                    print(f"✗ Error in {Path(migration_file).name}: {e}")
                    raise

        print(f"\n{'='*60}")
        print("Verifying database schema...")
        print(f"{'='*60}")

        tables_to_check = [
            'consumed_events',
            'consumed_media',
            'consumed_songs',
            'apple_music_sync_log'
        ]

        for table in tables_to_check:
            exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table}'
                )
            """)
            status = "✓" if exists else "✗"
            print(f"{status} Table '{table}': {'exists' if exists else 'NOT FOUND'}")

        print(f"\n{'='*60}")
        print("✓ All migrations completed!")
        print(f"{'='*60}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
