CREATE TABLE consumed_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  occurred_at TIMESTAMPTZ NOT NULL,
  day DATE NOT NULL,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  url TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX consumed_events_day_idx ON consumed_events(day DESC);
CREATE INDEX consumed_events_occurred_at_idx ON consumed_events(occurred_at DESC);
CREATE INDEX consumed_events_type_idx ON consumed_events(type);

CREATE TABLE consumed_media (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID NOT NULL REFERENCES consumed_events(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  width INT,
  height INT,
  bytes INT,
  content_type TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX consumed_media_event_id_idx ON consumed_media(event_id);
