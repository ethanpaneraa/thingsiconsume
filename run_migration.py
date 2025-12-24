import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: POSTGRES_URL or DATABASE_URL not set")
    exit(1)


async def run_migration():
    """Run the migration SQL file."""
    migration_file = "migrations/001_initial.sql"
    with open(migration_file, "r") as f:
        sql = f.read()

    print(f"Connecting to database...")
    conn = await asyncpg.connect(database_url)

    try:
        print("Running migration...")
        lines = []
        for line in sql.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('--'):
                lines.append(line)

        clean_sql = '\n'.join(lines)
        await conn.execute(clean_sql)

        print("✓ Migration completed successfully!")

        events_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'consumed_events'
            )
        """)

        media_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'consumed_media'
            )
        """)

        if events_exists and media_exists:
            print("✓ Tables verified: consumed_events and consumed_media exist")
        else:
            print("⚠ Warning: Tables may not have been created correctly")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())

