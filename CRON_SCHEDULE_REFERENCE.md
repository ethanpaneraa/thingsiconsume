# Cron Schedule Quick Reference

## Current Schedule

The workflow is currently set to run **every hour**:

```yaml
schedule:
  - cron: '0 * * * *'
```

## Cron Syntax

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

## Common Schedules

### Every Hour
```yaml
- cron: '0 * * * *'  # At minute 0 of every hour (current)
```

### Every 30 Minutes
```yaml
- cron: '*/30 * * * *'  # At minute 0 and 30 of every hour
```

### Every 2 Hours
```yaml
- cron: '0 */2 * * *'  # At minute 0 of every 2nd hour (12am, 2am, 4am...)
```

### Every 6 Hours
```yaml
- cron: '0 */6 * * *'  # At minute 0 of every 6th hour (12am, 6am, 12pm, 6pm)
```

### Once Per Day
```yaml
- cron: '0 0 * * *'  # At midnight UTC every day
- cron: '0 12 * * *'  # At noon UTC every day
```

### Multiple Times Per Day
```yaml
- cron: '0 0,12 * * *'  # At midnight and noon UTC
- cron: '0 8,12,18 * * *'  # At 8am, noon, and 6pm UTC
```

### Weekdays Only
```yaml
- cron: '0 9 * * 1-5'  # At 9am UTC, Monday through Friday
```

### Weekends Only
```yaml
- cron: '0 10 * * 0,6'  # At 10am UTC on Saturday and Sunday
```

## Important Notes

### Time Zone
- GitHub Actions cron runs in **UTC time zone**
- Convert your local time to UTC
- Example: 9am PST = 5pm UTC (during standard time)

### Minimum Interval
- GitHub Actions may delay scheduled workflows by up to 15 minutes
- Don't rely on exact timing for critical operations
- For high-frequency updates, consider webhooks or other triggers

### Cost Considerations

**Free tier limits:**
- Public repos: Unlimited minutes ✅
- Private repos: 2,000 minutes/month

**Estimated usage per schedule:**
- Each run: ~3 minutes
- Every hour (24/day): 2,160 minutes/month ⚠️ (exceeds free tier for private repos)
- Every 2 hours (12/day): 1,080 minutes/month ✅
- Every 6 hours (4/day): 360 minutes/month ✅

## How to Change the Schedule

1. Edit `.github/workflows/sync-and-deploy.yml`
2. Find the `schedule` section:
   ```yaml
   schedule:
     - cron: '0 * * * *'  # Change this line
   ```
3. Replace with your desired schedule
4. Commit and push:
   ```bash
   git add .github/workflows/sync-and-deploy.yml
   git commit -m "Update cron schedule"
   git push
   ```

## Testing Cron Expressions

Use [crontab.guru](https://crontab.guru/) to test and validate your cron expressions.

Examples:
- `0 * * * *` → [crontab.guru/#0_*_*_*_*](https://crontab.guru/#0_*_*_*_*)
- `*/30 * * * *` → [crontab.guru/#*/30_*_*_*_*](https://crontab.guru/#*/30_*_*_*_*)

## Recommended Schedules

### For Personal Use (Private Repo)
```yaml
- cron: '0 */6 * * *'  # Every 6 hours (saves minutes)
```

### For Public Repo (Unlimited)
```yaml
- cron: '0 * * * *'  # Every hour (current setting)
```

### For Low Activity
```yaml
- cron: '0 0,12 * * *'  # Twice per day
```

## Manual Triggers

You can always manually trigger the workflow:
1. Go to **Actions** tab on GitHub
2. Select "Sync Apple Music & Deploy to GitHub Pages"
3. Click **Run workflow**
4. Select branch and click **Run workflow**

This bypasses the schedule and runs immediately.

