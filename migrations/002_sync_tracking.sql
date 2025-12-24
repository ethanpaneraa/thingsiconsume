CREATE TABLE IF NOT EXISTS apple_music_sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    songs_fetched INT NOT NULL,
    songs_added INT NOT NULL,
    latest_song_id TEXT,
    api_song_ids JSONB,
    status TEXT NOT NULL CHECK (status IN ('success', 'error')),
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_sync_log_synced_at ON apple_music_sync_log(synced_at DESC);

