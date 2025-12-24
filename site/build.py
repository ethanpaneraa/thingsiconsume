"""
Build script to generate index.html from Postgres database (no templating engine).
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from html import escape

from dotenv import load_dotenv
import asyncpg

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Get database URL
database_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("POSTGRES_URL or DATABASE_URL environment variable not set")

# Base URL for images (so we can point to Cloudflare Worker or local dev worker)
# Examples:
# - For production: https://consumed.yourdomain.com
# - For local worker dev: http://127.0.0.1:8787
image_base_url = os.getenv("IMAGE_BASE_URL", "").rstrip("/")


async def fetch_events():
    """Fetch all events with media from database."""
    conn = await asyncpg.connect(database_url)

    try:
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
                    "occurred_at": row["occurred_at"].isoformat() if row["occurred_at"] else "",
                    "day": row["day"].isoformat() if row["day"] else "",
                    "type": row["type"],
                    "title": row["title"] or "",
                    "url": row["url"] or "",
                    "payload": row["payload"] or {},
                    "media": [],
                }

            # Add media if it exists
            if row["media_id"]:
                events_dict[event_id]["media"].append(
                    {
                        "id": str(row["media_id"]),
                        "path": row["media_path"],
                        "width": row["width"],
                        "height": row["height"],
                    }
                )

        return list(events_dict.values())

    finally:
        await conn.close()


async def fetch_songs():
    """Fetch all songs from database."""
    conn = await asyncpg.connect(database_url)

    try:
        rows = await conn.fetch(
            """
            SELECT
                id,
                played_at,
                day,
                title,
                artist,
                album,
                apple_music_url,
                artwork_url,
                duration_ms
            FROM consumed_songs
            ORDER BY day DESC, played_at DESC
            """
        )

        songs = []
        for row in rows:
            songs.append({
                "id": str(row["id"]),
                "occurred_at": row["played_at"].isoformat() if row["played_at"] else "",
                "day": row["day"].isoformat() if row["day"] else "",
                "type": "music",
                "title": row["title"] or "",
                "url": row["apple_music_url"] or "",
                "payload": {
                    "artist": row["artist"] or "",
                    "album": row["album"] or "",
                    "artwork_url": row["artwork_url"] or "",
                    "duration_ms": row["duration_ms"],
                },
                "media": [],
            })

        return songs

    finally:
        await conn.close()


def group_events_by_day(events):
    """Group events by day."""
    day_groups = defaultdict(list)

    for event in events:
        day = event["day"]
        day_groups[day].append(event)

    # Convert to list of dicts, sorted by day DESC
    result = [
        {"day": day, "events": events}
        for day, events in sorted(day_groups.items(), reverse=True)
    ]

    return result


def render_html(days):
    """Render full HTML page as a string (no templates)."""
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en">')
    parts.append("<head>")
    parts.append('    <meta charset="UTF-8">')
    parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    parts.append("    <title>Consumed</title>")
    parts.append('    <link rel="stylesheet" href="/assets/site.css">')
    parts.append("</head>")
    parts.append("<body>")
    parts.append("    <header>")
    parts.append("        <h1>Consumed</h1>")
    parts.append('        <p class="subtitle">A log of things consumed</p>')
    parts.append("    </header>")
    parts.append("")
    parts.append("    <main>")

    for day_group in days:
        day_label = escape(day_group["day"])
        parts.append('        <section class="day-section">')
        parts.append(f'            <h2 class="day-header">{day_label}</h2>')
        parts.append('            <div class="events-container">')

        for event in day_group["events"]:
            etype = escape(event["type"])
            title = escape(event["title"])
            url = event["url"]
            payload = event["payload"] or {}
            occurred_at = event["occurred_at"]

            parts.append(f'                <article class="event event-{etype}">')

            if etype in ["meal", "photo"] and event["media"]:
                parts.append('                    <div class="event-media">')
                for media in event["media"]:
                    raw_path = media["path"] or ""
                    # If IMAGE_BASE_URL is set, prefix it; otherwise keep the original path
                    if image_base_url:
                        full_url = f"{image_base_url}/{raw_path.lstrip('/')}"
                    else:
                        full_url = raw_path
                    src = escape(full_url)
                    width = media["width"]
                    height = media["height"]
                    attrs = [f'src="{src}"', f'alt="{title}"', 'loading="lazy"']
                    if width and height:
                        attrs.append(f'width="{width}"')
                        attrs.append(f'height="{height}"')
                    parts.append(f'                        <img {" ".join(attrs)}>')  # noqa: E501
                parts.append("                    </div>")
                parts.append(f'                    <h3 class="event-title">{title}</h3>')

            elif etype == "link":
                parts.append('                    <h3 class="event-title">')
                if url:
                    safe_url = escape(url)
                    parts.append(
                        f'                        <a href="{safe_url}" target="_blank" rel="noopener noreferrer">{title}</a>'
                    )
                else:
                    parts.append(f"                        {title}")
                parts.append("                    </h3>")
                if url:
                    parts.append(f'                    <p class="event-url">{escape(url)}</p>')

            elif etype == "video":
                parts.append(f'                    <h3 class="event-title">{title}</h3>')
                if url:
                    safe_url = escape(url)
                    parts.append("                    <p class=\"event-url\">")
                    parts.append(
                        f'                        <a href="{safe_url}" target="_blank" rel="noopener noreferrer">{safe_url}</a>'
                    )
                    parts.append("                    </p>")

            elif etype == "music":
                artist = payload.get("artist", "")
                if artist:
                    display_title = f"{title} - {escape(str(artist))}"
                else:
                    display_title = title
                parts.append(f'                    <h3 class="event-title">{display_title}</h3>')

            elif etype == "place":
                parts.append(f'                    <h3 class="event-title">{title}</h3>')
                address = payload.get("address")
                if address:
                    parts.append(f'                    <p class="event-address">{escape(str(address))}</p>')

            elif etype == "note":
                parts.append(f'                    <h3 class="event-title">{title}</h3>')
                text = payload.get("text")
                if text:
                    parts.append(f'                    <p class="event-text">{escape(str(text))}</p>')

            else:
                parts.append(f'                    <h3 class="event-title">{title}</h3>')

            # Time
            if occurred_at:
                safe_dt = escape(occurred_at)
                display = escape(occurred_at[:16])
                parts.append(f'                    <time class="event-time" datetime="{safe_dt}">{display}</time>')

            parts.append("                </article>")

        parts.append("            </div>")
        parts.append("        </section>")

    parts.append("    </main>")
    parts.append("")
    parts.append("    <footer>")
    parts.append(f"        <p>Last updated: {escape(datetime.now().isoformat())}</p>")
    parts.append("    </footer>")
    parts.append("</body>")
    parts.append("</html>")

    return "\n".join(parts)


async def main():
    """Main build function."""
    # Fetch events and songs
    print("Fetching events from database...")
    events = await fetch_events()
    print(f"Found {len(events)} events")

    print("Fetching songs from database...")
    songs = await fetch_songs()
    print(f"Found {len(songs)} songs")

    # Combine events and songs
    all_items = events + songs
    print(f"Total items: {len(all_items)}")

    # Group by day
    days = group_events_by_day(all_items)
    print(f"Grouped into {len(days)} days")

    # Prepare output directories
    output_dir = Path(__file__).parent / "docs"
    output_dir.mkdir(exist_ok=True)

    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    # Copy CSS
    css_source = Path(__file__).parent / "assets" / "site.css"
    css_dest = assets_dir / "site.css"
    if css_source.exists():
        import shutil
        shutil.copy2(css_source, css_dest)
        print(f"Copied CSS to {css_dest}")

    # Render HTML
    print("Rendering HTML...")
    html_content = render_html(days)

    # Write HTML
    output_file = output_dir / "index.html"
    output_file.write_text(html_content, encoding="utf-8")
    print(f"Generated {output_file}")

    print("Build complete!")


if __name__ == "__main__":
    import asyncio
    import sys

    # Python 3.6 compatibility
    if sys.version_info >= (3, 7):
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(main())
        finally:
            loop.close()

