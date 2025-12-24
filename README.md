# What I Consumed

A personal website for logging and displaying everything you consume - meals, links, videos, music, places, and more.

## Features

- 📸 **Image uploads** - Automatically processed and stored in Cloudflare R2
- 🍽️ **Meal tracking** - Log meals with photos
- 🔗 **Link saving** - Save interesting articles and websites
- 🎵 **Media tracking** - Log videos and music
- 🎵 **Apple Music integration** - Automatically sync songs you listen to
- 📍 **Place logging** - Remember places you've visited
- 📝 **Notes** - Add quick notes and thoughts
- 📱 **iPhone Shortcut** - Quick capture from your phone
- 🌐 **Static site** - Fast, beautiful timeline of your consumption

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for a step-by-step deployment guide.

### TL;DR

```bash
# 1. Deploy Cloudflare Worker
cd worker && wrangler login && wrangler deploy

# 2. Setup environment
cp .env.example .env
# Edit .env with your credentials

# 3. Run database migrations
python run_migration.py

# 4. Start the ingest API
docker-compose up -d ingest

# 5. Generate static site
cd site && python build.py
```

## Architecture

```
┌─────────────┐
│   iPhone    │
│  Shortcut   │
└──────┬──────┘
       │
       ↓ POST /v1/events
┌─────────────────┐         ┌──────────────┐
│   Ingest API    │────────→│  PostgreSQL  │
│   (FastAPI)     │         │   Database   │
└────────┬────────┘         └──────────────┘
         │
         │ Upload images
         ↓
┌─────────────────┐
│  Cloudflare R2  │
│   (Storage)     │
└────────┬────────┘
         │
         │ Serve via
         ↓
┌─────────────────┐
│ Cloudflare      │
│    Worker       │
└────────┬────────┘
         │
         ↓ Display images
┌─────────────────┐
│  Static Site    │
│   (Generated)   │
└─────────────────┘
```

## Components

### 1. Ingest API (`ingest/`)

FastAPI service that:

- Accepts consumption events via API
- Processes and resizes images to WebP
- Uploads images to Cloudflare R2
- Stores metadata in PostgreSQL

**Deploy to:** Railway, Fly.io, or Docker

### 2. Cloudflare Worker (`worker/`)

Edge function that:

- Serves images from R2 storage
- Adds caching headers
- Provides fast, global CDN delivery

**Deploy to:** Cloudflare Workers (free tier)

### 3. Site Builder (`site/`)

Python script that:

- Queries PostgreSQL for all events
- Generates static HTML
- Creates a beautiful timeline view

**Output:** Static HTML/CSS to deploy anywhere

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Detailed deployment guide
- **[IPHONE_SHORTCUT_SETUP.md](IPHONE_SHORTCUT_SETUP.md)** - Setup iPhone shortcut for quick capture
- **[worker/README.md](worker/README.md)** - Cloudflare Worker deployment

## Apple Music Integration

Track songs you listen to automatically! The app syncs with Apple Music API to display unique songs per day on your site.

### Quick Setup

1. **Get Apple Music tokens** (requires Apple Developer account)

   - Developer token (JWT) - lasts 6 months
   - User token - authenticates as you

2. **Add to `.env` file:**

   ```bash
   APPLE_DEVELOPER_TOKEN="your_jwt_token_here"
   APPLE_MUSIC_USER_TOKEN="your_user_token_here"
   ```

3. **Run migration:**

   ```bash
   python run_migration.py migrations/002_add_songs.sql
   ```

4. **Test authentication:**

   ```bash
   python test_apple_music_auth.py
   ```

5. **Sync songs:**

   ```bash
   python sync_apple_music.py
   ```

6. **Rebuild site:**
   ```bash
   cd site && python build.py
   ```

### How It Works

- **Unique songs per day**: If you listen to the same song 100 times in a day, it shows once
- **Automatic syncing**: Run `sync_apple_music.py` via cron to keep it updated
- **Rich display**: Shows album artwork, artist, album name, and links to Apple Music
- **API endpoint**: `POST /v1/songs/sync` to trigger sync programmatically

### Troubleshooting

If you get **401 Unauthorized** errors:

- Your tokens may have expired (developer tokens last 6 months)
- Run `python test_apple_music_auth.py` to diagnose
- Regenerate tokens using `test_recent.py` as reference

For detailed setup instructions, see the Apple Music API documentation.

## API Endpoints

### `POST /v1/events`

Create a non-media event (link, video, music, place, note)

```bash
curl -X POST https://your-api.com/v1/events \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "occurred_at": "2025-12-23T12:00:00-08:00",
    "type": "link",
    "title": "Interesting Article",
    "url": "https://example.com",
    "payload": {}
  }'
```

### `POST /v1/events/with-image`

Create a media event with image upload

```bash
curl -X POST https://your-api.com/v1/events/with-image \
  -H "X-API-Key: your-api-key" \
  -F 'metadata={"occurred_at":"2025-12-23T12:00:00-08:00","type":"meal","title":"Lunch"}' \
  -F 'file=@photo.jpg'
```

### `GET /health`

Health check endpoint

## Development

### Local Setup

```bash
# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env

# Run migrations
python run_migration.py

# Start ingest API
cd ingest
uvicorn app.main:app --reload

# Test locally
curl http://localhost:8000/health
```

### Local Worker Development

```bash
cd worker
npm install -g wrangler
wrangler dev
```

Access at `http://localhost:8787`

## Technology Stack

- **API**: FastAPI (Python)
- **Database**: PostgreSQL
- **Storage**: Cloudflare R2
- **CDN**: Cloudflare Workers
- **Image Processing**: Pillow
- **Frontend**: Static HTML/CSS
- **Deployment**: Docker, Railway, Fly.io, Cloudflare

## Environment Variables

See `.env.example` for all required variables:

- `POSTGRES_URL` - PostgreSQL connection string
- `INGEST_API_KEY` - API authentication key
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` - R2 credentials
- `R2_BUCKET_NAME` - R2 bucket name
- `IMAGE_BASE_URL` - Cloudflare Worker URL

## License

MIT

## Contributing

This is a personal project, but feel free to fork and adapt for your own use!
