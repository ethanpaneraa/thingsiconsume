import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import os

sys.path.insert(0, str(Path(__file__).parent / "ingest"))

from dotenv import load_dotenv
from app.apple_music import AppleMusicClient
from app.db import (
    get_db_connection,
    create_song,
    get_last_api_song_ids,
    create_sync_log,
    close_pool
)
import pytz

load_dotenv(override=True)


LA_TZ = pytz.timezone("America/Los_Angeles")


def derive_day(occurred_at: datetime) -> str:
    if occurred_at.tzinfo is None:
        occurred_at = pytz.utc.localize(occurred_at)

    la_time = occurred_at.astimezone(LA_TZ)
    return la_time.date().isoformat()


async def sync_songs():
    try:
        client = AppleMusicClient()
        await get_db_connection()

        songs = client.get_recently_played(limit=30)

        if not songs:
            print("⚠ No songs returned from API")
            return 0

        current_song_ids = [song.get("apple_music_id") for song in songs if song.get("apple_music_id")]

        previous_song_ids = await get_last_api_song_ids()

        if previous_song_ids is None:
            songs_to_add = songs
        elif current_song_ids == previous_song_ids:
            print("✓ No new music (API unchanged)")
            songs_to_add = []
        else:
            previous_set = set(previous_song_ids)
            songs_to_add = []

            for song in songs:
                song_id = song.get("apple_music_id")
                if song_id and song_id not in previous_set:
                    songs_to_add.append(song)

            print(f"Found {len(songs_to_add)} new song(s)")

        if not songs_to_add:
            await create_sync_log(
                songs_fetched=len(songs),
                songs_added=0,
                latest_song_id=songs[0].get("apple_music_id") if songs else None,
                api_song_ids=current_song_ids,
                status="success"
            )
            return 0

        new_songs_count = 0
        duplicate_count = 0
        skipped_count = 0

        now_utc = datetime.now(pytz.utc)
        today = derive_day(now_utc)

        for song_data in songs_to_add:
            if not song_data.get("title") or not song_data.get("artist"):
                skipped_count += 1
                continue

            position = song_data.get("position", 0)
            minutes_back = position * 4
            played_at = now_utc - timedelta(minutes=minutes_back)

            try:
                _, was_inserted = await create_song(
                    played_at=played_at,
                    day=today,
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
                if "duplicate key" not in str(e).lower():
                    print(f"  ✗ {song_data.get('title', 'Unknown')}: {str(e)[:80]}")
                else:
                    duplicate_count += 1
                skipped_count += 1

        await create_sync_log(
            songs_fetched=len(songs),
            songs_added=new_songs_count,
            latest_song_id=songs[0].get("apple_music_id") if songs else None,
            api_song_ids=current_song_ids,
            status="success"
        )

        if new_songs_count > 0:
            print(f"✓ Added {new_songs_count} song(s) to {today}")
        if duplicate_count > 0:
            print(f"  ({duplicate_count} already in database)")

        return new_songs_count

    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}")
        return 0
    finally:
        await close_pool()


def main():
    try:
        result = asyncio.run(sync_songs())
        sys.exit(0 if result >= 0 else 1)
    except KeyboardInterrupt:
        print("\nSync interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
