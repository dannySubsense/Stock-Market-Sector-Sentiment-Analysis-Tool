-- 1W timeframe sector sentiment table (close-to-close)

CREATE TABLE IF NOT EXISTS sector_sentiment_1w (
    sector VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    batch_id VARCHAR(50) NOT NULL,
    sentiment_score FLOAT,
    weighted_sentiment_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (sector, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_sector_sentiment_1w_time ON sector_sentiment_1w(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sector_sentiment_1w_batch ON sector_sentiment_1w(batch_id);

