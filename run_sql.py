import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run_sql():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    conn = await asyncpg.connect(database_url)

    try:
        # Drop and recreate the index
        await conn.execute("DROP INDEX IF EXISTS consumed_songs_unique_per_day_idx")
        print("Dropped old index")

        await conn.execute("""
            CREATE UNIQUE INDEX consumed_songs_unique_per_day_idx
            ON consumed_songs(apple_music_id, day)
            WHERE apple_music_id IS NOT NULL
        """)
        print("Created new index")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_sql())




