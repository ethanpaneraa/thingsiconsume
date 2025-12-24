import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def fix():
    database_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(database_url)

    try:
        # Drop the partial index
        await conn.execute("DROP INDEX IF EXISTS consumed_songs_unique_per_day_idx")
        print("Dropped partial index")

        # Create a full unique constraint instead
        # First, handle any NULL apple_music_ids by generating unique placeholders
        await conn.execute("""
            UPDATE consumed_songs
            SET apple_music_id = 'unknown-' || id::text
            WHERE apple_music_id IS NULL
        """)
        print("Updated NULL apple_music_ids")

        # Now create the unique constraint
        await conn.execute("""
            CREATE UNIQUE INDEX consumed_songs_unique_per_day_idx
            ON consumed_songs(apple_music_id, day)
        """)
        print("Created unique index (without WHERE clause)")

        print("\n✓ Database fixed! Try running sync again.")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix())

