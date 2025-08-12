-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create basic tables for market sentiment analysis (active tables only)
CREATE TABLE IF NOT EXISTS stock_universe (
    symbol VARCHAR(10) PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector VARCHAR(100) NOT NULL,
    market_cap BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- NOTE: legacy table stock_prices removed intentionally

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

-- NOTE: legacy table sector_sentiment removed intentionally

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_stock_universe_sector ON stock_universe(sector);
-- NOTE: removed legacy indexes for stock_prices and sector_sentiment

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO market_user; 