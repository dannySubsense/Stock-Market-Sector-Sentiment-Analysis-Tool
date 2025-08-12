-- 30-minute timeframe sector sentiment table (intraday)

CREATE TABLE IF NOT EXISTS sector_sentiment_30min (
    sector VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    batch_id VARCHAR(50) NOT NULL,
    sentiment_score FLOAT,
    weighted_sentiment_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (sector, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_sector_sentiment_30m_time ON sector_sentiment_30min(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sector_sentiment_30m_batch ON sector_sentiment_30min(batch_id);

-- Helpful composite index to speed latest snapshot queries
CREATE INDEX IF NOT EXISTS idx_stock_prices_1d_symbol_time ON stock_prices_1d(symbol, recorded_at DESC, fmp_timestamp DESC);

