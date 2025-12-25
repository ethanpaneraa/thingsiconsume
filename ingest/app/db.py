import os
import json
import asyncpg
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date, timedelta
import uuid

_pool: Optional[asyncpg.Pool] = None


async def get_db_connection() -> asyncpg.Pool:
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
                WHERE apple_music_id = $1
                  AND played_at BETWEEN $2 AND $3
                LIMIT 1
                """,
                apple_music_id,
                played_at - timedelta(minutes=10),
                played_at + timedelta(minutes=10)
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


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_last_api_song_ids() -> Optional[List[str]]:
    pool = await get_db_connection()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT api_song_ids
            FROM apple_music_sync_log
            WHERE status = 'success' AND api_song_ids IS NOT NULL
            ORDER BY synced_at DESC
            LIMIT 1
            """
        )

        if not row or not row["api_song_ids"]:
            return None

        return row["api_song_ids"]


async def create_sync_log(
    songs_fetched: int,
    songs_added: int,
    latest_song_id: Optional[str] = None,
    api_song_ids: Optional[List[str]] = None,
    status: str = "success",
    error_message: Optional[str] = None
) -> uuid.UUID:
    sync_id = uuid.uuid4()
    pool = await get_db_connection()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO apple_music_sync_log (
                id, songs_fetched, songs_added, latest_song_id, api_song_ids, status, error_message
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
            """,
            sync_id,
            songs_fetched,
            songs_added,
            latest_song_id,
            json.dumps(api_song_ids) if api_song_ids else None,
            status,
            error_message
        )

    return sync_id

