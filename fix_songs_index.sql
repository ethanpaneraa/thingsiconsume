-- Drop the existing partial index if it exists
DROP INDEX IF EXISTS consumed_songs_unique_per_day_idx;

-- Create the unique index that the code expects
CREATE UNIQUE INDEX consumed_songs_unique_per_day_idx
ON consumed_songs(apple_music_id, day)
WHERE apple_music_id IS NOT NULL;




