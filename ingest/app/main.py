from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
import os
import json
from .db import get_db_connection, create_event, create_media
from .r2 import upload_to_r2
from .image_processing import convert_to_webp
import uuid
from datetime import datetime
import pytz

app = FastAPI(title="Consumed API", version="1.0.0")

# Timezone for day calculation
LA_TZ = pytz.timezone("America/Los_Angeles")


@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool on startup."""
    from .db import get_db_connection
    await get_db_connection()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection pool on shutdown."""
    from .db import close_pool
    await close_pool()


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key from header."""
    expected_key = os.getenv("INGEST_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


def derive_day(occurred_at: datetime) -> str:
    """Convert occurred_at to America/Los_Angeles timezone and extract day."""
    if occurred_at.tzinfo is None:
        # Assume UTC if no timezone info
        occurred_at = pytz.utc.localize(occurred_at)

    # Convert to LA timezone
    la_time = occurred_at.astimezone(LA_TZ)
    return la_time.date().isoformat()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/v1/events")
async def create_event_endpoint(
    event_data: dict,
    api_key: str = Depends(verify_api_key)
):
    """
    Create a non-media event (link, video, music, place, note).

    Request body:
    {
        "occurred_at": "2025-12-22T16:10:00-08:00",
        "type": "link",
        "title": "Postgres JSONB indexing tips",
        "url": "https://example.com/post",
        "payload": {}
    }
    """
    try:
        # Parse occurred_at
        occurred_at_str = event_data.get("occurred_at")
        if not occurred_at_str:
            raise HTTPException(status_code=400, detail="occurred_at is required")

        occurred_at = datetime.fromisoformat(occurred_at_str.replace("Z", "+00:00"))
        day = derive_day(occurred_at)

        # Validate required fields
        event_type = event_data.get("type")
        title = event_data.get("title")
        if not event_type or not title:
            raise HTTPException(status_code=400, detail="type and title are required")

        # Create event
        event_id = await create_event(
            occurred_at=occurred_at,
            day=day,
            event_type=event_type,
            title=title,
            url=event_data.get("url"),
            payload=event_data.get("payload", {})
        )

        return {"id": str(event_id), "day": day}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")


@app.post("/v1/events/with-image")
async def create_event_with_image(
    metadata: str = Form(...),
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Create a media event and upload image.

    Multipart form:
    - metadata: JSON string with event data
    - file: binary image file
    """
    try:
        # Parse metadata
        event_data = json.loads(metadata)

        # Parse occurred_at
        occurred_at_str = event_data.get("occurred_at")
        if not occurred_at_str:
            raise HTTPException(status_code=400, detail="occurred_at is required in metadata")

        occurred_at = datetime.fromisoformat(occurred_at_str.replace("Z", "+00:00"))
        day = derive_day(occurred_at)

        # Validate required fields
        event_type = event_data.get("type")
        title = event_data.get("title")
        if not event_type or not title:
            raise HTTPException(status_code=400, detail="type and title are required in metadata")

        # Read and convert image
        image_bytes = await file.read()
        webp_bytes, width, height = convert_to_webp(image_bytes)

        # Generate paths
        event_id = uuid.uuid4()
        media_id = uuid.uuid4()
        year = occurred_at.strftime("%Y")
        month = occurred_at.strftime("%m")
        day_str = occurred_at.strftime("%d")

        # R2 key: images/YYYY/MM/DD/<eventId>/<mediaId>.webp
        r2_key = f"images/{year}/{month}/{day_str}/{event_id}/{media_id}.webp"

        # Upload to R2
        upload_to_r2(r2_key, webp_bytes, "image/webp")

        # Path for response (URL path)
        media_path = f"/images/{year}/{month}/{day_str}/{event_id}/{media_id}.webp"

        # Create event in database
        await create_event(
            occurred_at=occurred_at,
            day=day,
            event_type=event_type,
            title=title,
            url=event_data.get("url"),
            payload=event_data.get("payload", {}),
            event_id=event_id
        )

        # Create media record
        await create_media(
            event_id=event_id,
            path=media_path,
            width=width,
            height=height,
            bytes=len(webp_bytes),
            content_type="image/webp",
            media_id=media_id
        )

        return {
            "event_id": str(event_id),
            "media": {
                "path": media_path
            }
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in metadata")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event with image: {str(e)}")

