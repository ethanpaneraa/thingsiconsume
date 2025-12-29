"""
Script to reprocess existing images with correct EXIF orientation.
This will download images from R2, apply orientation fixes, and re-upload them.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path to import from ingest
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import asyncpg
from ingest.app.image_processing import convert_to_webp
from ingest.app.r2 import get_s3_client, upload_to_r2  # type: ignore

load_dotenv()

database_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("POSTGRES_URL or DATABASE_URL environment variable not set")


async def fix_existing_images():
    """Reprocess all existing images to fix orientation."""
    
    # Connect to database
    conn = await asyncpg.connect(database_url)
    
    try:
        # Get all media records
        media_records = await conn.fetch(
            """
            SELECT id, path, event_id
            FROM consumed_media
            ORDER BY id
            """
        )
        
        print(f"Found {len(media_records)} images to process")
        
        # Get R2 client and bucket name
        s3_client = get_s3_client()
        bucket_name = os.getenv("R2_BUCKET_NAME")
        
        if not bucket_name:
            raise ValueError("R2_BUCKET_NAME environment variable not set")
        
        fixed_count = 0
        error_count = 0
        
        for idx, record in enumerate(media_records, 1):
            media_id = record['id']
            path = record['path']
            
            print(f"[{idx}/{len(media_records)}] Processing {path}...")
            
            try:
                # Download the image from R2
                response = s3_client.get_object(Bucket=bucket_name, Key=path)
                image_bytes = response['Body'].read()
                
                if not image_bytes:
                    print(f"  ❌ Could not download {path}")
                    error_count += 1
                    continue
                
                # Reprocess with orientation fix
                webp_bytes, width, height = convert_to_webp(image_bytes, quality=90)
                
                # Upload back to R2 (overwrite existing)
                upload_to_r2(path, webp_bytes, "image/webp")
                
                # Update dimensions in database
                await conn.execute(
                    """
                    UPDATE consumed_media
                    SET width = $1, height = $2
                    WHERE id = $3
                    """,
                    width, height, media_id
                )
                print(f"  ✅ Fixed {path} ({width}x{height})")
                fixed_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error processing {path}: {e}")
                error_count += 1
                continue
        
        print("\n" + "="*60)
        print(f"Processing complete!")
        print(f"  ✅ Fixed: {fixed_count}")
        print(f"  ❌ Errors: {error_count}")
        print(f"  📊 Total: {len(media_records)}")
        print("="*60)
        
    finally:
        await conn.close()


if __name__ == "__main__":
    print("Starting image orientation fix...")
    print("This will reprocess all existing images to apply correct orientation.\n")
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        sys.exit(0)
    
    asyncio.run(fix_existing_images())
    print("\nDone!")
