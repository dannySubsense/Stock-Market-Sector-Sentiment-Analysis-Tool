-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create basic tables for market sentiment analysis
CREATE TABLE IF NOT EXISTS stock_universe (
    symbol VARCHAR(10) PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector VARCHAR(100) NOT NULL,
    market_cap BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stock_prices (
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(10, 4),
    high_price DECIMAL(10, 4),
    low_price DECIMAL(10, 4),
    close_price DECIMAL(10, 4),
    volume BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Convert stock_prices to hypertable for time-series optimization
SELECT create_hypertable('stock_prices', 'timestamp', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS stock_prices_1d (
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(10, 4),
    high_price DECIMAL(10, 4),
    low_price DECIMAL(10, 4),
    close_price DECIMAL(10, 4),
    volume BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Convert stock_prices_1d to hypertable for time-series optimization
SELECT create_hypertable('stock_prices_1d', 'timestamp', if_not_exists => TRUE);

-- Create index for stock_prices_1d
CREATE INDEX IF NOT EXISTS idx_stock_prices_1d_symbol_timestamp ON stock_prices_1d(symbol, timestamp);

CREATE TABLE IF NOT EXISTS sector_sentiment (
    sector VARCHAR(100) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    sentiment_score DECIMAL(5, 4),
    bullish_count INTEGER,
    bearish_count INTEGER,
    total_volume BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sector, timeframe, timestamp)
);

-- Convert sector_sentiment to hypertable
SELECT create_hypertable('sector_sentiment', 'timestamp', if_not_exists => TRUE);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_stock_universe_sector ON stock_universe(sector);
CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_timestamp ON stock_prices(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_sector_sentiment_sector_timeframe ON sector_sentiment(sector, timeframe);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO market_user; 