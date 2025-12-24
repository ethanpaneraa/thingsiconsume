import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_and_fix():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    conn = await asyncpg.connect(database_url)

    try:
        # Check if table exists
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'consumed_songs'
            )
        """)
        print(f"Table exists: {exists}")

        if not exists:
            print("Creating table...")
            await conn.execute("""
                CREATE TABLE consumed_songs (
                  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  apple_music_id TEXT,
                  isrc TEXT,
                  title TEXT NOT NULL,
                  artist TEXT NOT NULL,
                  album TEXT,
                  album_artist TEXT,
                  duration_ms INT,
                  genre TEXT,
                  release_date DATE,
                  apple_music_url TEXT,
                  artwork_url TEXT,
                  played_at TIMESTAMPTZ NOT NULL,
                  day DATE NOT NULL,
                  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            print("Table created")

        # Check indexes
        indexes = await conn.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'consumed_songs'
        """)
        print(f"\nCurrent indexes:")
        for idx in indexes:
            print(f"  {idx['indexname']}")

        # Drop and recreate the unique index
        print("\nRecreating unique index...")
        await conn.execute("DROP INDEX IF EXISTS consumed_songs_unique_per_day_idx")
        await conn.execute("""
            CREATE UNIQUE INDEX consumed_songs_unique_per_day_idx
            ON consumed_songs(apple_music_id, day)
            WHERE apple_music_id IS NOT NULL
        """)
        print("Index created")

        # Verify it exists
        idx_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_indexes
                WHERE indexname = 'consumed_songs_unique_per_day_idx'
            )
        """)
        print(f"Index exists: {idx_exists}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_and_fix())




