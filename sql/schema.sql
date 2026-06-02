CREATE TABLE IF NOT EXISTS verdict_cache (
    ticker      TEXT PRIMARY KEY,
    verdict     JSONB NOT NULL,
    made_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS predictions (
    id            SERIAL PRIMARY KEY,
    ticker        TEXT NOT NULL,
    predicted_on  DATE NOT NULL,
    prediction    TEXT NOT NULL,       -- bullish / neutral / bearish
    for_date      DATE NOT NULL,       -- the day being predicted
    actual_move   NUMERIC,             -- filled by nightly job
    correct       BOOLEAN              -- filled by nightly job
);

CREATE TABLE IF NOT EXISTS accuracy (
    scope       TEXT NOT NULL,         -- 'overall' or agent name
    period      TEXT NOT NULL,         -- e.g. 'last_30_days'
    hit_rate    NUMERIC NOT NULL,
    total       INT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (scope, period)
);

CREATE TABLE IF NOT EXISTS discovery_list (
    kind        TEXT NOT NULL,         -- 'movers' or 'most_viewed'
    payload     JSONB NOT NULL,        -- ranked list
    built_on    DATE NOT NULL,
    PRIMARY KEY (kind, built_on)
);

CREATE TABLE IF NOT EXISTS ticker_views (
    ticker      TEXT PRIMARY KEY,
    views       INT NOT NULL DEFAULT 0,
    last_asked  TIMESTAMPTZ NOT NULL DEFAULT now()
);
