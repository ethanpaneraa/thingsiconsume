import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from html import escape

from dotenv import load_dotenv
import asyncpg

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

database_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("POSTGRES_URL or DATABASE_URL environment variable not set")

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

    result = [
        {"day": day, "events": events}
        for day, events in sorted(day_groups.items(), reverse=True)
    ]

    return result


def format_day_label(day_str):
    """Format day string like 'tuesday, november 18th'."""
    try:
        dt = datetime.strptime(day_str, "%Y-%m-%d")
        day_name = dt.strftime("%A").lower()
        month_name = dt.strftime("%B").lower()
        day_num = dt.day
        if 10 <= day_num % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day_num % 10, 'th')
        return f"{day_name}, {month_name} {day_num}{suffix}"
    except:
        return day_str


def render_html(days):
    """Render full HTML page as a string (no templates)."""
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en">')
    parts.append("<head>")
    parts.append('    <meta charset="UTF-8">')
    parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    parts.append("    <title>thing that i consumed</title>")
    parts.append('    <link rel="stylesheet" href="assets/site.css">')
    parts.append("</head>")
    parts.append("<body>")
    parts.append('    <div class="center">')
    parts.append('        <h1 class="title">consumed</h1>')
    parts.append('        <p class="subtitle">a daily index of the things that i consume</p>')

    for idx, day_group in enumerate(days):
        day_label = format_day_label(day_group["day"])
        parts.append('        <details class="day">')
        parts.append(f'            <summary class="date">{escape(day_label)}</summary>')

        categories = {
            "physical": [],
            "audio": [],
            "video": [],
            "text": [],
            "places": []
        }

        for event in day_group["events"]:
            etype = event["type"]
            if etype in ["meal", "photo"]:
                categories["physical"].append(event)
            elif etype == "music":
                categories["audio"].append(event)
            elif etype == "video":
                categories["video"].append(event)
            elif etype == "place":
                categories["places"].append(event)
            else:
                categories["text"].append(event)

        for category_name, category_events in categories.items():
            if not category_events:
                continue

            parts.append('            <details>')
            parts.append(f'                <summary>{category_name}</summary>')

            for event in category_events:
                etype = event["type"]
                title = escape(event["title"]).lower()
                url = event["url"]
                payload = event["payload"] if isinstance(event["payload"], dict) else {}

                if etype in ["meal", "photo"] and event["media"]:
                    for media in event["media"]:
                        raw_path = media["path"] or ""
                        if image_base_url:
                            full_url = f"{image_base_url}/{raw_path.lstrip('/')}"
                        else:
                            full_url = raw_path
                        src = escape(full_url)
                        parts.append(f'                <img loading="lazy" src="{src}">')

                elif etype == "music":
                    artist = escape(str(payload.get("artist", ""))).lower()
                    if artist:
                        parts.append(f'                {title} - {artist}<br>')
                    else:
                        parts.append(f'                {title}<br>')

                elif etype == "video":
                    if url:
                        safe_url = escape(url)
                        parts.append(f'                <a href="{safe_url}">{title}</a><br>')
                    else:
                        parts.append(f'                {title}<br>')

                elif etype == "link":
                    if url:
                        safe_url = escape(url)
                        parts.append(f'                <a href="{safe_url}">{title}</a><br>')
                    else:
                        parts.append(f'                {title}<br>')

                elif etype == "place":
                    address = escape(str(payload.get("address", ""))).lower()
                    if url:
                        safe_url = escape(url)
                        if address:
                            parts.append(f'                <a href="{safe_url}">{title}</a> - {address}<br>')
                        else:
                            parts.append(f'                <a href="{safe_url}">{title}</a><br>')
                    else:
                        if address:
                            parts.append(f'                {title} - {address}<br>')
                        else:
                            parts.append(f'                {title}<br>')

                elif etype == "note":
                    text = escape(str(payload.get("text", ""))).lower()
                    if text:
                        parts.append(f'                {title} - {text}<br>')
                    else:
                        parts.append(f'                {title}<br>')

                else:
                    parts.append(f'                {title}<br>')

            parts.append("            </details>")

        parts.append("        </details>")

    parts.append("    </div>")
    parts.append("")
    parts.append("    <footer>")
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

    days = group_events_by_day(all_items)
    print(f"Grouped into {len(days)} days")

    output_dir = Path(__file__).parent / "docs"
    output_dir.mkdir(exist_ok=True)

    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    css_source = Path(__file__).parent / "assets" / "site.css"
    css_dest = assets_dir / "site.css"
    if css_source.exists():
        import shutil
        shutil.copy2(css_source, css_dest)
        print(f"Copied CSS to {css_dest}")

    print("Rendering HTML...")
    html_content = render_html(days)

    output_file = output_dir / "index.html"
    output_file.write_text(html_content, encoding="utf-8")
    print(f"Generated {output_file}")

    cname_file = output_dir / "CNAME"
    cname_file.write_text("consumed.ethanpinedaa.dev\n", encoding="utf-8")
    print(f"Generated {cname_file}")

    print("Build complete!")


if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

