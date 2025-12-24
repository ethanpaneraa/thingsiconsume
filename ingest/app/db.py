import os
import json
import asyncpg
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date
import uuid

_pool: Optional[asyncpg.Pool] = None


async def get_db_connection() -> asyncpg.Pool:
    """Get or create database connection pool."""
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        _pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=10
        )
    return _pool


async def create_event(
    occurred_at: datetime,
    day: str,
    event_type: str,
    title: str,
    url: Optional[str] = None,
    payload: Dict[str, Any] = None,
    event_id: Optional[uuid.UUID] = None
) -> uuid.UUID:
    """Create an event in the database."""

    if payload is None:
        payload = {}

    if event_id is None:
        event_id = uuid.uuid4()

    pool = await get_db_connection()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO consumed_events (id, occurred_at, day, type, title, url, payload)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            """,
            event_id,
            occurred_at,
            date.fromisoformat(day),
            event_type,
            title,
            url,
            json.dumps(payload)
        )

    return event_id


async def create_media(
    event_id: uuid.UUID,
    path: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    bytes: Optional[int] = None,
    content_type: Optional[str] = None,
    media_id: Optional[uuid.UUID] = None
) -> uuid.UUID:
    """Create a media record in the database."""
    if media_id is None:
        media_id = uuid.uuid4()

    pool = await get_db_connection()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO consumed_media (id, event_id, path, width, height, bytes, content_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            media_id,
            event_id,
            path,
            width,
            height,
            bytes,
            content_type
        )

    return media_id


async def create_song(
    played_at: datetime,
    day: str,
    title: str,
    artist: str,
    album: Optional[str] = None,
    apple_music_id: Optional[str] = None,
    isrc: Optional[str] = None,
    duration_ms: Optional[int] = None,
    release_date: Optional[str] = None,
    apple_music_url: Optional[str] = None,
    artwork_url: Optional[str] = None,
    payload: Dict[str, Any] = None
) -> Tuple[uuid.UUID, bool]:
    """
    Create a song record in the database.

    Returns:
        Tuple of (song_id, was_inserted) where was_inserted is True if new, False if duplicate
    """
    if payload is None:
        payload = {}

    song_id = uuid.uuid4()
    pool = await get_db_connection()

    release_date_obj = None
    if release_date:
        release_date_obj = date.fromisoformat(release_date)

    async with pool.acquire() as conn:
        if apple_music_id:
            existing = await conn.fetchrow(
                """
                SELECT id FROM consumed_songs
                WHERE apple_music_id = $1 AND day = $2
                """,
                apple_music_id,
                date.fromisoformat(day)
            )
        else:
            existing = await conn.fetchrow(
                """
                SELECT id FROM consumed_songs
                WHERE played_at = $1 AND title = $2 AND artist = $3
                """,
                played_at,
                title,
                artist
            )

        if existing:
            return existing["id"], False

        # Insert new song
        await conn.execute(
            """
            INSERT INTO consumed_songs (
                id, played_at, day, title, artist, album,
                apple_music_id, isrc, duration_ms, release_date,
                apple_music_url, artwork_url, payload
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb)
            """,
            song_id,
            played_at,
            date.fromisoformat(day),
            title,
            artist,
            album,
            apple_music_id,
            isrc,
            duration_ms,
            release_date_obj,
            apple_music_url,
            artwork_url,
            json.dumps(payload)
        )

        return song_id, True


async def get_latest_song_timestamp() -> Optional[datetime]:
    """Get the timestamp of the most recently played song."""
    pool = await get_db_connection()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT MAX(played_at) as latest_played_at
            FROM consumed_songs
            """
        )

        return row["latest_played_at"] if row else None


async def close_pool():
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_all_events_with_media() -> List[Dict[str, Any]]:
    """
    Get all events with their associated media, ordered by day DESC, occurred_at DESC.
    Returns list of dictionaries with event and media data.
    """
    pool = await get_db_connection()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                e.id as event_id,
                e.occurred_at,
                e.day,
                e.type,
                e.title,
                e.url,
                e.payload,
                m.id as media_id,
                m.path as media_path,
                m.width,
                m.height
            FROM consumed_events e
            LEFT JOIN consumed_media m ON m.event_id = e.id
            ORDER BY e.day DESC, e.occurred_at DESC
            """
        )

    # Group by event (since one event can have multiple media)
    events_dict = {}
    for row in rows:
        event_id = str(row["event_id"])
        if event_id not in events_dict:
            events_dict[event_id] = {
                "id": event_id,
                "occurred_at": row["occurred_at"].isoformat(),
                "day": row["day"].isoformat(),
                "type": row["type"],
                "title": row["title"],
                "url": row["url"],
                "payload": row["payload"],
                "media": []
            }

        # Add media if it exists
        if row["media_id"]:
            events_dict[event_id]["media"].append({
                "id": str(row["media_id"]),
                "path": row["media_path"],
                "width": row["width"],
                "height": row["height"]
            })

    return list(events_dict.values())

