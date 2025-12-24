#!/bin/bash
# Test script to simulate the GitHub Actions workflow locally

set -e  # Exit on error

echo "=========================================="
echo "Testing Workflow Locally"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Create a .env file with:"
    echo "  APPLE_DEVELOPER_TOKEN=..."
    echo "  APPLE_MUSIC_USER_TOKEN=..."
    echo "  POSTGRES_URL=..."
    exit 1
fi

echo "✓ Found .env file"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
pip install -q asyncpg python-dotenv pytz
echo "✓ Dependencies installed"
echo ""

# Test sync
echo "=========================================="
echo "Step 1: Testing Apple Music Sync"
echo "=========================================="
python sync_apple_music.py
echo ""

# Test build
echo "=========================================="
echo "Step 2: Testing Site Build"
echo "=========================================="
cd site
python build.py
cd ..
echo ""

# Check output
if [ -f "site/docs/index.html" ]; then
    echo "=========================================="
    echo "✅ SUCCESS!"
    echo "=========================================="
    echo ""
    echo "Generated files:"
    ls -lh site/docs/
    echo ""
    echo "To view the site locally:"
    echo "  open site/docs/index.html"
    echo ""
    echo "Or serve it with Python:"
    echo "  cd site/docs && python3 -m http.server 8000"
    echo "  Then visit: http://localhost:8000"
else
    echo "❌ Error: index.html was not generated"
    exit 1
fi

