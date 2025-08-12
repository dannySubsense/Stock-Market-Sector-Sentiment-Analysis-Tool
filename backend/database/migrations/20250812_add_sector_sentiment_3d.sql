-- 3D timeframe sector sentiment table (minimal schema mirroring 1D)
-- Retention: 180 days; Compression: after 14 days (if using TimescaleDB policies)

CREATE TABLE IF NOT EXISTS sector_sentiment_3d (
    sector VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    batch_id VARCHAR(50) NOT NULL,
    sentiment_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (sector, timestamp)
);

-- Indexes to support queries
CREATE INDEX IF NOT EXISTS idx_sector_sentiment_3d_time ON sector_sentiment_3d(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sector_sentiment_3d_batch ON sector_sentiment_3d(batch_id);

-- Optional TimescaleDB retention/compression policies (no hypertable needed for minimal usage)
-- Uncomment if you decide to convert to hypertable later
-- SELECT add_retention_policy('sector_sentiment_3d', INTERVAL '180 days');
-- SELECT add_compression_policy('sector_sentiment_3d', INTERVAL '14 days');



