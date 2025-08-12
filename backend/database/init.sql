-- =============================================================================
-- TimescaleDB Initialization Script
-- Market Sector Sentiment Analysis Tool - Production Schema
-- =============================================================================

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- =============================================================================
-- STOCK UNIVERSE TABLE (Standard PostgreSQL)
-- =============================================================================
CREATE TABLE stock_universe (
    symbol VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    market_cap BIGINT NOT NULL,
    avg_daily_volume BIGINT NOT NULL,
    current_price DECIMAL(10,4) NOT NULL,
    sector VARCHAR(50) NOT NULL,
    original_fmp_sector VARCHAR(100),
    volatility_multiplier DECIMAL(3,2) DEFAULT 1.0,
    gap_frequency VARCHAR(20) DEFAULT 'medium',
    float_shares BIGINT,
    shortability_score DECIMAL(3,2),
    is_active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_stock_universe_sector ON stock_universe(sector);
CREATE INDEX idx_stock_universe_active ON stock_universe(is_active);
CREATE INDEX idx_stock_universe_market_cap ON stock_universe(market_cap);
CREATE INDEX idx_stock_universe_sector_active ON stock_universe(sector, is_active);

-- =============================================================================
-- SECTOR SENTIMENT TABLE (TimescaleDB Hypertable)
-- =============================================================================
CREATE TABLE sector_sentiment (
    id SERIAL,
    sector VARCHAR(50) NOT NULL,
    sentiment_score DECIMAL(6,4) NOT NULL,
    color_classification VARCHAR(20) NOT NULL,
    confidence_level DECIMAL(4,3) NOT NULL,
    
    -- Multi-timeframe data
    timeframe_30min DECIMAL(8,4),
    timeframe_1day DECIMAL(8,4),
    timeframe_3day DECIMAL(8,4),
    timeframe_1week DECIMAL(8,4),
    
    -- Top stocks (JSON)
    top_bullish_stocks JSONB,
    top_bearish_stocks JSONB,
    
    -- Metadata
    analysis_type VARCHAR(20) DEFAULT 'sector_sentiment',
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (created_at, sector)
);

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable('sector_sentiment', 'created_at', chunk_time_interval => INTERVAL '1 day');

-- Indexes for time-series queries
CREATE INDEX idx_sector_sentiment_sector_time ON sector_sentiment(sector, created_at DESC);
CREATE INDEX idx_sector_sentiment_color ON sector_sentiment(color_classification, created_at DESC);

-- =============================================================================
-- STOCK DATA TABLE (TimescaleDB Hypertable for historical data)
-- =============================================================================
CREATE TABLE stock_data (
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10,4) NOT NULL,
    volume BIGINT NOT NULL,
    open_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    close_price DECIMAL(10,4),
    
    -- Volume metrics
    avg_volume_20d BIGINT,
    volume_ratio DECIMAL(6,3),
    
    -- Performance metrics
    performance_1d DECIMAL(8,4),
    performance_3d DECIMAL(8,4),
    performance_1w DECIMAL(8,4),
    
    -- Technical indicators
    rsi DECIMAL(5,2),
    volatility DECIMAL(6,4),
    
    -- Metadata
    data_source VARCHAR(20),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (timestamp, symbol)
);

-- Convert to hypertable
SELECT create_hypertable('stock_data', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Indexes for stock data queries
CREATE INDEX idx_stock_data_symbol_time ON stock_data(symbol, timestamp DESC);
CREATE INDEX idx_stock_data_performance ON stock_data(performance_1d, timestamp DESC);

-- =============================================================================
-- STOCK PRICES 1D TABLE (TimescaleDB Hypertable for daily price history)
-- =============================================================================
--
-- Stock Prices 1D Table Schema Documentation
--
-- This table stores 1-day OHLCV and related market data for all tracked symbols, matching the FMP Multiple Company Prices API response.
--
-- Data Types and Formats
--
-- | Field                | SQL Type         | Notes                                                                 |
-- |----------------------|------------------|-----------------------------------------------------------------------|
-- | symbol               | VARCHAR(10)      | Primary key (with fmp_timestamp)                                      |
-- | name                 | VARCHAR(200)     | Company name                                                          |
-- | price                | DOUBLE PRECISION | Last trade price                                                      |
-- | changes_percentage   | DOUBLE PRECISION | % change from previous close                                          |
-- | change               | DOUBLE PRECISION | Absolute price change                                                 |
-- | day_low              | DOUBLE PRECISION | Day’s low                                                             |
-- | day_high             | DOUBLE PRECISION | Day’s high                                                            |
-- | year_high            | DOUBLE PRECISION | 52-week high                                                          |
-- | year_low             | DOUBLE PRECISION | 52-week low                                                           |
-- | market_cap           | BIGINT           | Market capitalization                                                 |
-- | price_avg_50         | DOUBLE PRECISION | 50-day average price                                                  |
-- | price_avg_200        | DOUBLE PRECISION | 200-day average price                                                 |
-- | exchange             | VARCHAR(20)      | Exchange code                                                         |
-- | volume               | BIGINT           | Current day’s volume                                                  |
-- | avg_volume           | BIGINT           | 50-day average volume                                                 |
-- | open_price           | DOUBLE PRECISION | Opening price                                                         |
-- | previous_close       | DOUBLE PRECISION | Previous day’s close                                                  |
-- | eps                  | DOUBLE PRECISION | Earnings per share                                                    |
-- | pe                   | DOUBLE PRECISION | Price/earnings ratio                                                  |
-- | earnings_announcement| TIMESTAMP NULL   | Parsed ISO string to UTC datetime if possible                         |
-- | shares_outstanding   | BIGINT           | Number of shares                                                      |
-- | fmp_timestamp        | BIGINT           | FMP’s UNIX timestamp (primary key with symbol)                        |
-- | recorded_at          | TIMESTAMP        | UTC timestamp when record was inserted                                |
--
-- Table Definition
CREATE TABLE IF NOT EXISTS stock_prices_1d (
    symbol VARCHAR(10) NOT NULL,
    fmp_timestamp BIGINT NOT NULL,
    name VARCHAR(200),
    price DOUBLE PRECISION,
    changes_percentage DOUBLE PRECISION,
    change DOUBLE PRECISION,
    day_low DOUBLE PRECISION,
    day_high DOUBLE PRECISION,
    year_high DOUBLE PRECISION,
    year_low DOUBLE PRECISION,
    market_cap BIGINT,
    price_avg_50 DOUBLE PRECISION,
    price_avg_200 DOUBLE PRECISION,
    exchange VARCHAR(20),
    volume BIGINT,
    avg_volume BIGINT,
    open_price DOUBLE PRECISION,
    previous_close DOUBLE PRECISION,
    eps DOUBLE PRECISION,
    pe DOUBLE PRECISION,
    earnings_announcement TIMESTAMPTZ NULL,
    shares_outstanding BIGINT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, fmp_timestamp)
);

-- Convert to TimescaleDB hypertable for time-series optimization
SELECT create_hypertable('stock_prices_1d', 'recorded_at', chunk_time_interval => INTERVAL '1 day');

-- Indexes for fast queries
CREATE INDEX idx_stock_prices_1d_symbol_time ON stock_prices_1d(symbol, recorded_at DESC);
CREATE INDEX idx_stock_prices_1d_timestamp ON stock_prices_1d(recorded_at DESC);

-- =============================================================================
-- DATA RETENTION POLICIES (7-day retention as specified in plan)
-- =============================================================================

-- Sector sentiment: Keep detailed data for 90 days
SELECT add_retention_policy('sector_sentiment', INTERVAL '90 days');

-- Stock data: Keep detailed data for 90 days  
SELECT add_retention_policy('stock_data', INTERVAL '90 days');

-- Stock prices 1d: Keep detailed data for 7 days (as per plan)
SELECT add_retention_policy('stock_prices_1d', INTERVAL '7 days');

-- =============================================================================
-- COMPRESSION POLICIES (Compress after 2 days for stock_prices_1d)
-- =============================================================================

-- Compress sector sentiment data after 7 days
SELECT add_compression_policy('sector_sentiment', INTERVAL '7 days');

-- Compress stock data after 7 days
SELECT add_compression_policy('stock_data', INTERVAL '7 days');

-- Compress stock prices 1d after 2 days (as per plan)
SELECT add_compression_policy('stock_prices_1d', INTERVAL '2 days');

-- =============================================================================
-- INITIAL SEED DATA
-- =============================================================================

-- Insert initial sector records for the 11 FMP sectors
INSERT INTO sector_sentiment (sector, sentiment_score, color_classification, confidence_level, analysis_type) VALUES
('basic_materials', 0.0, 'blue_neutral', 0.5, 'initialization'),
('communication_services', 0.0, 'blue_neutral', 0.5, 'initialization'),
('consumer_cyclical', 0.0, 'blue_neutral', 0.5, 'initialization'),
('consumer_defensive', 0.0, 'blue_neutral', 0.5, 'initialization'),
('energy', 0.0, 'blue_neutral', 0.5, 'initialization'),
('financial_services', 0.0, 'blue_neutral', 0.5, 'initialization'),
('healthcare', 0.0, 'blue_neutral', 0.5, 'initialization'),
('industrials', 0.0, 'blue_neutral', 0.5, 'initialization'),
('real_estate', 0.0, 'blue_neutral', 0.5, 'initialization'),
('technology', 0.0, 'blue_neutral', 0.5, 'initialization'),
('utilities', 0.0, 'blue_neutral', 0.5, 'initialization');

-- =============================================================================
-- PERFORMANCE OPTIMIZATION
-- =============================================================================

-- Analyze tables for query optimization
ANALYZE stock_universe;
ANALYZE sector_sentiment;
ANALYZE stock_data;

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Current sector sentiment view (latest data per sector)
CREATE VIEW current_sector_sentiment AS
SELECT DISTINCT ON (sector) 
    sector,
    sentiment_score,
    color_classification,
    confidence_level,
    timeframe_30min,
    timeframe_1day,
    timeframe_3day,
    timeframe_1week,
    top_bullish_stocks,
    top_bearish_stocks,
    last_updated
FROM sector_sentiment 
ORDER BY sector, created_at DESC;

-- Active stocks by sector view
CREATE VIEW active_stocks_by_sector AS
SELECT 
    sector,
    COUNT(*) as stock_count,
    AVG(market_cap) as avg_market_cap,
    SUM(avg_daily_volume) as total_volume
FROM stock_universe 
WHERE is_active = TRUE
GROUP BY sector
ORDER BY stock_count DESC;

-- =============================================================================
-- GRANTS AND PERMISSIONS
-- =============================================================================

-- Grant necessary permissions to sentiment_user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sentiment_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sentiment_user;
GRANT SELECT ON ALL TABLES IN SCHEMA timescaledb_information TO sentiment_user;
GRANT SELECT ON ALL TABLES IN SCHEMA timescaledb_experimental TO sentiment_user;

-- =============================================================================
-- INITIALIZATION COMPLETE
-- =============================================================================

-- Log successful initialization
INSERT INTO sector_sentiment (sector, sentiment_score, color_classification, confidence_level, analysis_type)
VALUES ('_system', 1.0, 'dark_green', 1.0, 'database_initialized');

COMMIT; 

-- =============================================================================
-- 1D TABLES (Validated Pipeline Minimal Schema)
-- =============================================================================

-- sector_sentiment_1d: minimal schema per validated 1D pipeline
CREATE TABLE IF NOT EXISTS sector_sentiment_1d (
    sector VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    batch_id VARCHAR(50) NOT NULL,
    sentiment_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (sector, timestamp)
);

-- sector_gappers_1d: top gainers/losers per sector (rank 1..3)
CREATE TABLE IF NOT EXISTS sector_gappers_1d (
    sector VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    gapper_type VARCHAR(10) NOT NULL,
    rank INTEGER NOT NULL,
    batch_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    changes_percentage FLOAT NOT NULL,
    volume BIGINT NOT NULL,
    current_price FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (sector, timestamp, gapper_type, rank)
);