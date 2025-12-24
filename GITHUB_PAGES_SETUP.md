# GitHub Pages Setup Guide

This guide will help you set up automatic syncing and deployment of your "What I Consumed" site to GitHub Pages.

## Overview

The GitHub Actions workflow will:

- ✅ Run every hour automatically (via cron schedule)
- ✅ Run on every commit to the `main` branch
- ✅ Sync your Apple Music listening history
- ✅ Build the static HTML site
- ✅ Deploy to GitHub Pages

## Prerequisites

1. A GitHub repository for this project
2. Apple Music Developer Token and User Token
3. PostgreSQL database (e.g., Neon, Supabase, or Railway)
4. Cloudflare R2 or similar for images (optional)

## Step 1: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under "Build and deployment":
   - **Source**: Select "GitHub Actions"
   - This allows the workflow to deploy directly

## Step 2: Add Repository Secrets

Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add the following secrets:

### Required Secrets:

1. **`APPLE_DEVELOPER_TOKEN`**

   - Your Apple Music Developer Token (JWT)
   - Generate using `generate_token.py`
   - Valid for 6 months

2. **`APPLE_MUSIC_USER_TOKEN`**

   - Your Apple Music User Token
   - Get this from the auth flow (see `auth.html`)
   - Valid for 6 months

3. **`POSTGRES_URL`** or **`DATABASE_URL`**
   - Your PostgreSQL connection string
   - Format: `postgresql://user:password@host:port/database`
   - Example: `postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/consumed`

### Optional Secrets:

4. **`IMAGE_BASE_URL`** (optional)
   - Base URL for your images (e.g., Cloudflare Worker URL)
   - Example: `https://consumed.yourdomain.com`
   - Leave empty if not using external image hosting

## Step 3: Verify Workflow File

The workflow file should be at: `.github/workflows/sync-and-deploy.yml`

It's already created and includes:

- Cron schedule: `0 * * * *` (every hour at minute 0)
- Push trigger: runs on commits to `main`
- Manual trigger: can be run manually from Actions tab

## Step 4: Push to GitHub

```bash
git add .
git commit -m "Add GitHub Actions workflow for hourly sync and deployment"
git push origin main
```

## Step 5: Monitor the Workflow

1. Go to the **Actions** tab in your repository
2. You should see the workflow running
3. Click on a run to see detailed logs
4. First run might take 2-3 minutes

## Step 6: Access Your Site

After the first successful deployment:

- Your site will be available at: `https://[username].github.io/[repo-name]/`
- Example: `https://ethanpineda.github.io/whaticonsumed/`

## Workflow Schedule

The workflow runs:

- **Every hour**: At minute 0 (12:00 AM, 1:00 AM, 2:00 AM, etc.)
- **On every commit**: When you push to the `main` branch
- **Manually**: Click "Run workflow" in the Actions tab

## Customizing the Schedule

To change the cron schedule, edit `.github/workflows/sync-and-deploy.yml`:

```yaml
schedule:
  - cron: "0 * * * *" # Every hour
  # - cron: '*/30 * * * *'  # Every 30 minutes
  # - cron: '0 */2 * * *'  # Every 2 hours
  # - cron: '0 0 * * *'  # Once per day at midnight
```

Cron syntax: `minute hour day month weekday`

## Troubleshooting

### Workflow fails on sync step

- Check that your Apple Music tokens are valid (they expire after 6 months)
- Verify database connection string is correct
- The workflow continues even if sync fails (`continue-on-error: true`)

### Workflow fails on build step

- Check database connection
- Verify `site/build.py` exists and is working locally
- Check workflow logs for specific Python errors

### Site not updating

- Check the Actions tab for failed workflows
- Verify GitHub Pages is enabled and set to "GitHub Actions"
- Check that secrets are properly set

### Manual trigger

If you want to force a sync/deploy:

1. Go to **Actions** tab
2. Click "Sync Apple Music & Deploy to GitHub Pages"
3. Click "Run workflow" → "Run workflow"

## Local Testing

Before pushing, test locally:

```bash
# Test sync
python sync_apple_music.py

# Test build
cd site
python build.py

# Check generated HTML
open site/docs/index.html
```

## Token Renewal

Apple Music tokens expire after 6 months. When they expire:

1. **Developer Token**: Regenerate using `generate_token.py`
2. **User Token**: Get new token via `auth.html` flow
3. Update the secrets in GitHub repository settings

## Cost Considerations

- GitHub Actions: 2,000 free minutes/month for private repos
- This workflow uses ~2-3 minutes per run
- 24 runs/day × 30 days = 720 runs/month = ~2,160 minutes/month
- **Recommendation**: Use a public repository (unlimited free minutes)

## Security Notes

- Never commit tokens or database credentials to the repository
- Always use GitHub Secrets for sensitive data
- Tokens are masked in workflow logs
- Consider using environment-specific tokens (dev vs prod)

## Next Steps

1. ✅ Enable GitHub Pages
2. ✅ Add all required secrets
3. ✅ Push the workflow file
4. ✅ Monitor first run
5. ✅ Visit your deployed site
6. 🎉 Enjoy automatic updates every hour!
