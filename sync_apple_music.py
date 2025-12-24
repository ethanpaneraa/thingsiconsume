import asyncio
import sys
from pathlib import Path
from datetime import datetime
import os

sys.path.insert(0, str(Path(__file__).parent / "ingest"))

from dotenv import load_dotenv
from app.apple_music import AppleMusicClient
from app.db import (
    get_db_connection,
    create_song,
    close_pool
)
import pytz

load_dotenv(override=True)
print("DEV token loaded:", bool(os.getenv("APPLE_DEVELOPER_TOKEN")))
print("USER token loaded:", bool(os.getenv("APPLE_MUSIC_USER_TOKEN")))
print("DEV token prefix:", (os.getenv("APPLE_DEVELOPER_TOKEN") or "")[:16])
print("USER token prefix:", (os.getenv("APPLE_MUSIC_USER_TOKEN") or "")[:16])


LA_TZ = pytz.timezone("America/Los_Angeles")


def derive_day(occurred_at: datetime) -> str:
    if occurred_at.tzinfo is None:
        occurred_at = pytz.utc.localize(occurred_at)

    la_time = occurred_at.astimezone(LA_TZ)
    return la_time.date().isoformat()


async def sync_songs():
    print("Starting Apple Music sync...")
    print(f"Timestamp: {datetime.now().isoformat()}")

    try:
        print("Initializing Apple Music client...")
        client = AppleMusicClient()

        print("Connecting to database...")
        await get_db_connection()

        print("Fetching songs from Apple Music...")
        songs = client.get_recently_played(limit=30)

        print(f"Found {len(songs)} songs to process")

        new_songs_count = 0
        duplicate_count = 0
        skipped_count = 0

        for song_data in songs:
            if not song_data.get("title") or not song_data.get("artist"):
                skipped_count += 1
                continue

            played_at_str = song_data.get("played_at")
            if not played_at_str:
                played_at = datetime.now(pytz.utc)
            else:
                played_at = datetime.fromisoformat(played_at_str.replace("Z", "+00:00"))

            day = derive_day(played_at)

            try:
                _, was_inserted = await create_song(
                    played_at=played_at,
                    day=day,
                    title=song_data["title"],
                    artist=song_data["artist"],
                    album=song_data.get("album"),
                    apple_music_id=song_data.get("apple_music_id"),
                    isrc=song_data.get("isrc"),
                    duration_ms=song_data.get("duration_ms"),
                    release_date=song_data.get("release_date"),
                    apple_music_url=song_data.get("apple_music_url"),
                    artwork_url=song_data.get("artwork_url"),
                    payload=song_data.get("payload", {})
                )
                if was_inserted:
                    new_songs_count += 1
                    print(f"  ✓ {song_data['title']} - {song_data['artist']}")
                else:
                    duplicate_count += 1
            except Exception as e:
                print(f"  ✗ Error adding song: {e}")
                skipped_count += 1

        print("\n" + "="*60)
        print(f"Sync complete!")
        print(f"  New songs added: {new_songs_count}")
        print(f"  Already in DB: {duplicate_count}")
        print(f"  Errors: {skipped_count}")
        print(f"  Total from API: {len(songs)}")
        print("="*60)

        return new_songs_count

    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nMake sure you have set the following environment variables:")
        print("  - APPLE_DEVELOPER_TOKEN")
        print("  - APPLE_MUSIC_USER_TOKEN")
        print("  - DATABASE_URL or POSTGRES_URL")
        return 0
    except Exception as e:
        print(f"Error during sync: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        # Close database connection
        await close_pool()


def main():
    """Main entry point."""
    try:
        result = asyncio.run(sync_songs())
        sys.exit(0 if result >= 0 else 1)
    except KeyboardInterrupt:
        print("\nSync interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()

