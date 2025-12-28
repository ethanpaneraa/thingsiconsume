import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Add parent directory to path to import from ingest
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()


async def cleanup_database(cutoff_date, dry_run: bool = False):
    """
    Delete all data before the specified cutoff date.

    Args:
        cutoff_date: Delete all data before this date (exclusive) - datetime.date object
        dry_run: If True, only show what would be deleted without actually deleting
    """
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not database_url:
        raise ValueError("DATABASE_URL or POSTGRES_URL environment variable not set")

    conn = await asyncpg.connect(database_url)

    try:
        print(f"{'[DRY RUN] ' if dry_run else ''}Cleaning up data before {cutoff_date}...")
        print("-" * 60)

        # Start a transaction
        async with conn.transaction():
            # Count events to be deleted
            events_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM consumed_events
                WHERE day < $1
                """,
                cutoff_date

            )
            print(f"Events to delete: {events_count}")

            # Count media to be deleted (associated with those events)
            media_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM consumed_media m
                WHERE EXISTS (
                    SELECT 1 FROM consumed_events e
                    WHERE e.id = m.event_id AND e.day < $1
                )
                """,
                cutoff_date
            )
            print(f"Media items to delete: {media_count}")

            # Count songs to be deleted
            songs_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM consumed_songs
                WHERE day < $1
                """,
                cutoff_date
            )
            print(f"Songs to delete: {songs_count}")

            # Show breakdown by event type
            print("\nBreakdown by event type:")
            event_types = await conn.fetch(
                """
                SELECT type, COUNT(*) as count
                FROM consumed_events
                WHERE day < $1
                GROUP BY type
                ORDER BY count DESC
                """,
                cutoff_date
            )
            for row in event_types:
                print(f"  - {row['type']}: {row['count']}")

            print("-" * 60)

            if dry_run:
                print("\n[DRY RUN] No data was deleted. Run without --dry-run to actually delete.")
                # Rollback the transaction
                raise Exception("Dry run - rolling back")

            # Confirm deletion
            print("\n⚠️  WARNING: This will permanently delete the data listed above!")
            response = input("Type 'DELETE' to confirm: ")

            if response != "DELETE":
                print("Deletion cancelled.")
                raise Exception("User cancelled")

            # Delete media first (foreign key constraint)
            deleted_media = await conn.execute(
                """
                DELETE FROM consumed_media
                WHERE event_id IN (
                    SELECT id FROM consumed_events WHERE day < $1
                )
                """,
                cutoff_date
            )
            print(f"\n✓ Deleted {deleted_media.split()[-1]} media items")

            # Delete events
            deleted_events = await conn.execute(
                """
                DELETE FROM consumed_events
                WHERE day < $1
                """,
                cutoff_date
            )
            print(f"✓ Deleted {deleted_events.split()[-1]} events")

            # Delete songs
            deleted_songs = await conn.execute(
                """
                DELETE FROM consumed_songs
                WHERE day < $1
                """,
                cutoff_date
            )
            print(f"✓ Deleted {deleted_songs.split()[-1]} songs")

            print(f"\n✅ Cleanup complete! All data before {cutoff_date} has been deleted.")

    except Exception as e:
        if "Dry run" in str(e) or "User cancelled" in str(e):
            # Expected exceptions for dry run or cancellation
            pass
        else:
            print(f"\n❌ Error during cleanup: {e}")
            raise
    finally:
        await conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up database by deleting data before a specific date"
    )
    parser.add_argument(
        "--date",
        type=str,
        default="2025-12-24",
        help="Delete all data before this date (format: YYYY-MM-DD, default: 2025-12-24)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )

    args = parser.parse_args()

    try:
        cutoff_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD format.")
        sys.exit(1)

    print(f"Database Cleanup Script")
    print(f"Cutoff date: {cutoff_date}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    asyncio.run(cleanup_database(cutoff_date, dry_run=args.dry_run))


if __name__ == "__main__":
    main()

