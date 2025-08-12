-- =============================================================================
-- Phase 2 Signal Metrics Migration
-- Market Sector Sentiment Analysis Tool - Performance Tracking
-- =============================================================================

-- Create sector signal metrics table for performance tracking
CREATE TABLE sector_signal_metrics (
    id SERIAL PRIMARY KEY,
    sector VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Core signal characteristics
    sentiment_score DECIMAL(6,4) NOT NULL,
    confidence_level DECIMAL(4,3) NOT NULL,
    sample_size INTEGER NOT NULL,
    
    -- Statistical quality indicators
    outliers_removed INTEGER NOT NULL DEFAULT 0,
    significance_test_passed BOOLEAN NOT NULL DEFAULT FALSE,
    sample_size_warning BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Volume and market context
    total_volume BIGINT NOT NULL DEFAULT 0,
    bullish_count INTEGER NOT NULL DEFAULT 0,
    bearish_count INTEGER NOT NULL DEFAULT 0,
    
    -- Performance attribution (1D focus)
    volume_weighted_contribution DECIMAL(6,4) NOT NULL DEFAULT 0.0,
    statistical_confidence_factor DECIMAL(6,4) NOT NULL DEFAULT 0.0,
    data_quality_score DECIMAL(6,4) NOT NULL DEFAULT 0.0,
    
    -- Historical context (optional)
    rolling_accuracy_7d DECIMAL(6,4),
    rolling_accuracy_30d DECIMAL(6,4),
    signal_consistency_score DECIMAL(6,4),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to TimescaleDB hypertable for time-series performance
SELECT create_hypertable('sector_signal_metrics', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Create indexes for optimal query performance
CREATE INDEX idx_sector_timestamp ON sector_signal_metrics(sector, timestamp DESC);
CREATE INDEX idx_timestamp_desc ON sector_signal_metrics(timestamp DESC);
CREATE INDEX idx_sector_confidence ON sector_signal_metrics(sector, confidence_level DESC);
CREATE INDEX idx_performance_metrics ON sector_signal_metrics(
    rolling_accuracy_7d DESC, 
    signal_consistency_score DESC
);

-- Add retention policy: Keep detailed signal metrics for 180 days
-- (Longer than sector sentiment for performance analysis)
SELECT add_retention_policy('sector_signal_metrics', INTERVAL '180 days');

-- Add compression policy: Compress after 14 days
SELECT add_compression_policy('sector_signal_metrics', INTERVAL '14 days');

-- Create view for latest signal quality per sector
CREATE VIEW latest_sector_signal_quality AS
SELECT DISTINCT ON (sector)
    sector,
    sentiment_score,
    confidence_level,
    sample_size,
    outliers_removed,
    significance_test_passed,
    sample_size_warning,
    total_volume,
    bullish_count,
    bearish_count,
    volume_weighted_contribution,
    statistical_confidence_factor,
    data_quality_score,
    rolling_accuracy_7d,
    rolling_accuracy_30d,
    signal_consistency_score,
    timestamp as last_analysis
FROM sector_signal_metrics
ORDER BY sector, timestamp DESC;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON sector_signal_metrics TO sentiment_user;
GRANT SELECT ON latest_sector_signal_quality TO sentiment_user;

-- Analyze for query optimization
ANALYZE sector_signal_metrics;

COMMIT; 