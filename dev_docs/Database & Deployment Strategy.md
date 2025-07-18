# Market Sector Sentiment Analysis Tool

## Database & Deployment Strategy - Slice 1A Foundation & Slice 1B Framework

**Version:** 2.0 - Aligned with Slice Implementation Strategy  
**Target Environment:** Development → Local Server → Small Group → Cloud Scale  
**Slice 1A Focus:** 8-sector traffic light dashboard with <1s performance  
**Slice 1B Focus:** Theme intelligence and manipulation detection  
**Deployment Philosophy:** Progressive enhancement with clear migration paths

## Executive Summary

This database and deployment strategy is specifically tailored for the **two-slice implementation approach**, ensuring Slice 1A delivers immediate trading value while building the data foundation for Slice 1B's sophisticated intelligence capabilities. The strategy prioritizes **performance optimization for small-cap sector analysis** and **scalable architecture for theme detection**.

### Key Strategy Pillars - Slice Aligned:

- **Slice 1A Database:** Optimized for <1s sector grid performance with 1,500 stock universe
- **Slice 1B Extension:** Advanced time-series for theme tracking and correlation analysis
- **Progressive Deployment:** Local Development → Local Server → Small Group → Cloud Scale
- **Performance Targets:** Slice 1A (<1s grid, <5min analysis) + Slice 1B (<24hr themes, <100ms updates)
- **Migration Ready:** Database schema designed for Slice 1B enhancement without rewrites

## Database Architecture - Slice Implementation Strategy

### Slice 1A Database Foundation

#### Core Schema for Sector Dashboard

```sql
-- =====================================================
-- SLICE 1A: SECTOR SENTIMENT FOUNDATION
-- =====================================================
CREATE TABLE sector_sentiment_1a (
    timestamp TIMESTAMPTZ NOT NULL,
    sector VARCHAR(50) NOT NULL,
    sentiment_score DECIMAL(4,3) NOT NULL,  -- -1.0 to +1.0
    color_code VARCHAR(15) NOT NULL,        -- RED/BLUE/GREEN system
    confidence DECIMAL(4,3) NOT NULL,       -- 0.0 to 1.0
    stocks_count INTEGER NOT NULL,
    performance_30min DECIMAL(8,4),         -- Multi-timeframe tracking
    performance_1day DECIMAL(8,4),
    performance_3day DECIMAL(8,4),
    performance_1week DECIMAL(8,4),
    volume_weighted_change DECIMAL(8,4),
    relative_strength_vs_iwm DECIMAL(6,3),  -- vs Russell 2000
    top_bullish_stocks JSONB,               -- Top 3 gainers
    top_bearish_stocks JSONB,               -- Top 3 losers
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    slice_version VARCHAR(10) DEFAULT '1A',
    PRIMARY KEY (timestamp, sector)
);

SELECT create_hypertable('sector_sentiment_1a', 'timestamp',
    chunk_time_interval => INTERVAL '1 day');

-- Optimized indexes for Slice 1A performance
CREATE INDEX idx_sector_current ON sector_sentiment_1a (sector, timestamp DESC);
CREATE INDEX idx_color_classification ON sector_sentiment_1a (color_code, timestamp DESC);
```

#### Small-Cap Universe Table

```sql
-- =====================================================
-- SLICE 1A: DYNAMIC STOCK UNIVERSE ($10M - $2B)
-- =====================================================
CREATE TABLE stock_universe_1a (
    symbol VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255),
    market_cap BIGINT,                      -- $10M - $2B filter
    avg_daily_volume_20d BIGINT,            -- 1M+ requirement
    current_price DECIMAL(10,4),
    float_shares BIGINT,                    -- Shortability factor
    sector VARCHAR(50),                     -- 8 core sectors
    volatility_multiplier DECIMAL(3,1),    -- Sector-specific weighting
    gap_frequency_score DECIMAL(3,1),      -- Historical gap behavior
    exchange VARCHAR(20),                   -- NASDAQ/NYSE only
    last_universe_update TIMESTAMPTZ,
    slice_1a_eligible BOOLEAN DEFAULT TRUE,
    inclusion_reason VARCHAR(100),
    CONSTRAINT valid_market_cap CHECK (market_cap BETWEEN 10000000 AND 2000000000),
    CONSTRAINT valid_volume CHECK (avg_daily_volume_20d >= 1000000),
    CONSTRAINT valid_price CHECK (current_price >= 2.00)
);

-- Performance indexes for Slice 1A
CREATE INDEX idx_sector_market_cap ON stock_universe_1a (sector, market_cap);
CREATE INDEX idx_volume_filter ON stock_universe_1a (avg_daily_volume_20d DESC);
```

### Slice 1B Intelligence Extension

#### Theme Detection Tables

```sql
-- =====================================================
-- SLICE 1B: THEME INTELLIGENCE EXTENSION
-- =====================================================
CREATE TABLE theme_detection_1b (
    theme_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    theme_name VARCHAR(100) NOT NULL,       -- 'bitcoin_treasury', 'ai_transformation'
    emergence_timestamp TIMESTAMPTZ,
    detection_confidence DECIMAL(4,3),
    primary_sector VARCHAR(50),             -- Origin sector
    contaminated_sectors JSONB,             -- Cross-sector spread
    temperature_status VARCHAR(20),         -- COLD/WARM/HOT/EXTREME
    manipulation_risk_score DECIMAL(4,3),  -- 0.0-1.0 risk assessment
    sympathy_network JSONB,                 -- Related stock correlations
    narrative_sources JSONB,                -- SEC filings, news, social
    peak_intensity_reached BOOLEAN DEFAULT FALSE,
    cooling_phase_started TIMESTAMPTZ,
    slice_version VARCHAR(10) DEFAULT '1B',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('theme_detection_1b', 'emergence_timestamp',
    chunk_time_interval => INTERVAL '7 days');
```

#### Temperature Monitoring System

```sql
-- =====================================================
-- SLICE 1B: HOURLY TEMPERATURE TRACKING (4AM-8PM)
-- =====================================================
CREATE TABLE temperature_monitoring_1b (
    timestamp TIMESTAMPTZ NOT NULL,
    theme_id UUID REFERENCES theme_detection_1b(theme_id),
    stock_symbol VARCHAR(10),
    hourly_price_change DECIMAL(8,4),
    hourly_volume_multiple DECIMAL(6,2),    -- vs average volume
    temperature_classification VARCHAR(20), -- COLD/WARM/HOT/EXTREME
    momentum_velocity DECIMAL(8,4),         -- Rate of change acceleration
    squeeze_risk_indicator DECIMAL(4,3),    -- Short squeeze probability
    trading_recommendation VARCHAR(50),     -- Action guidance
    slice_version VARCHAR(10) DEFAULT '1B',
    PRIMARY KEY (timestamp, theme_id, stock_symbol)
);

SELECT create_hypertable('temperature_monitoring_1b', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour');
```

## Performance Optimization - Slice Specific

### Slice 1A Performance Requirements

```python
SLICE_1A_PERFORMANCE_TARGETS = {
    'sector_grid_load': {
        'target': '<1_second',
        'implementation': 'redis_pre_calculation',
        'cache_duration': '30_minutes',
        'fallback': 'graceful_degradation_to_2s'
    },
    'universe_refresh': {
        'target': 'daily_8pm_et',
        'scope': '1500_stocks_maximum',
        'validation': 'market_cap_volume_filters',
        'completion_time': '<5_minutes'
    },
    'multi_timeframe_calc': {
        'target': '<2_seconds_per_sector',
        'timeframes': ['30min', '1day', '3day', '1week'],
        'benchmark_comparison': 'russell_2000_iwm',
        'caching_strategy': 'progressive_cache_warming'
    }
}
```

### Slice 1B Intelligence Performance

```python
SLICE_1B_PERFORMANCE_TARGETS = {
    'theme_detection': {
        'target': '<24_hours_emergence_to_detection',
        'sources': ['sec_edgar', 'news_feeds', 'social_sentiment'],
        'processing': 'real_time_streaming_analysis',
        'confidence_threshold': '0.7_minimum'
    },
    'temperature_monitoring': {
        'target': '<100ms_status_updates',
        'frequency': 'hourly_4am_to_8pm',
        'scope': 'all_theme_related_stocks',
        'alert_latency': '<30_seconds'
    },
    'sympathy_prediction': {
        'target': '<5_minutes_correlation_analysis',
        'network_size': '1500_stock_universe',
        'prediction_accuracy': '>90_percent_target',
        'update_frequency': 'every_significant_move'
    }
}
```

## Redis Caching Strategy - Slice Optimized

### Slice 1A Cache Structure

```python
# Redis keys for Slice 1A performance
SLICE_1A_CACHE_KEYS = {
    'sector_grid': 'sector:grid:current',           # <1s loading
    'sector_detail': 'sector:{sector}:detail',     # Individual sector data
    'top_stocks': 'sector:{sector}:top_stocks',    # Top 3 bull/bear
    'universe_list': 'universe:stocks:current',    # 1,500 stock list
    'performance_matrix': 'perf:multi_timeframe',  # 30m/1d/3d/1w
    'background_status': 'analysis:background:status' # Scheduler state
}

# Cache TTL strategy
CACHE_TTL_STRATEGY = {
    'sector_grid': 1800,        # 30 minutes
    'sector_detail': 900,       # 15 minutes
    'top_stocks': 600,          # 10 minutes
    'universe_list': 86400,     # 24 hours (daily refresh)
    'performance_matrix': 300,  # 5 minutes
    'background_status': 60     # 1 minute
}
```

### Slice 1B Cache Enhancement

```python
# Additional Redis keys for Slice 1B
SLICE_1B_CACHE_KEYS = {
    'active_themes': 'themes:active:current',      # Current themes
    'temperature_grid': 'temp:grid:hourly',        # Temperature matrix
    'sympathy_networks': 'networks:correlations',  # Sympathy mappings
    'manipulation_alerts': 'alerts:manipulation',  # Active warnings
    'theme_contamination': 'themes:contamination'  # Cross-sector spread
}
```

## Deployment Pipeline - Slice Progression

### Phase 1: Slice 1A Local Development (Week 1)

```bash
#!/bin/bash
# scripts/setup-slice1a-environment.sh
set -e

echo "🚀 Setting up Slice 1A Foundation Environment"

# Core database setup for sector dashboard
docker run -d --name postgres-slice1a \
  -p 5432:5432 \
  -e POSTGRES_DB=market_sentiment_slice1a \
  -e POSTGRES_USER=slice1a_user \
  -e POSTGRES_PASSWORD=slice1a_dev_password \
  -v $(pwd)/data/slice1a:/var/lib/postgresql/data \
  timescale/timescaledb:latest-pg15

# Redis for <1s sector grid performance
docker run -d --name redis-slice1a \
  -p 6379:6379 \
  -v $(pwd)/data/redis-slice1a:/data \
  redis:alpine redis-server --appendonly yes --maxmemory 512mb

# Initialize Slice 1A schema
echo "📊 Creating Slice 1A optimized schema..."
psql postgresql://slice1a_user:slice1a_dev_password@localhost:5432/market_sentiment_slice1a \
  -f database/slice1a_schema.sql

echo "✅ Slice 1A environment ready for sector dashboard development"
```

### Phase 2: Slice 1A Production (Weeks 2-4)

```yaml
# docker-compose.slice1a.yml
version: "3.8"
services:
  postgres-slice1a:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: market_sentiment_slice1a
      POSTGRES_USER: ${SLICE1A_DB_USER}
      POSTGRES_PASSWORD: ${SLICE1A_DB_PASSWORD}
    volumes:
      - /opt/market-sentiment/data/slice1a:/var/lib/postgresql/data
      - ./database/slice1a_schema.sql:/docker-entrypoint-initdb.d/slice1a.sql
    command: |
      postgres
      -c shared_preload_libraries=timescaledb
      -c max_connections=100
      -c shared_buffers=512MB
      -c effective_cache_size=2GB
      -c work_mem=16MB
    restart: unless-stopped

  backend-slice1a:
    build:
      context: ./backend
      dockerfile: Dockerfile.slice1a
    environment:
      - SLICE_VERSION=1A
      - DATABASE_URL=${SLICE1A_DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - POLYGON_API_KEY=${POLYGON_API_KEY}
      - UNIVERSE_SIZE_LIMIT=1500
      - SECTOR_COUNT=8
    ports:
      - "8000:8000"
    restart: unless-stopped
```

### Phase 3: Slice 1B Extension (Weeks 5-14)

```bash
#!/bin/bash
# scripts/upgrade-to-slice1b.sh
set -e

echo "🧠 Upgrading to Slice 1B Intelligence Framework"

# Extend database schema for theme detection
echo "📈 Adding Slice 1B intelligence tables..."
psql $SLICE1A_DATABASE_URL -f database/slice1b_extension.sql

# Update application configuration
echo "🔧 Enabling Slice 1B features..."
export SLICE_VERSION="1B"
export THEME_DETECTION_ENABLED="true"
export TEMPERATURE_MONITORING_ENABLED="true"
export MANIPULATION_DETECTION_ENABLED="true"

# Deploy enhanced application
docker-compose -f docker-compose.slice1b.yml up -d

echo "✅ Slice 1B intelligence framework activated"
```

## Monitoring & Performance Validation

### Slice 1A Metrics Dashboard

```python
SLICE_1A_MONITORING = {
    'performance_metrics': {
        'sector_grid_load_time': '<1000ms',
        'on_demand_analysis_time': '<300000ms',  # 5 minutes
        'background_analysis_completion': '<300000ms',
        'universe_refresh_time': '<300000ms',
        'redis_cache_hit_ratio': '>95%'
    },
    'business_metrics': {
        'sector_prediction_accuracy': '>75%',
        'universe_coverage': '1500_stocks',
        'uptime_during_market_hours': '>99.5%',
        'user_session_length': '>15_minutes',
        'feature_adoption_rate': '>80%'
    }
}
```

### Slice 1B Intelligence Metrics

```python
SLICE_1B_MONITORING = {
    'intelligence_metrics': {
        'theme_detection_latency': '<86400000ms',  # 24 hours
        'manipulation_avoidance_accuracy': '>80%',
        'sympathy_prediction_accuracy': '>90%',
        'temperature_update_latency': '<100ms',
        'false_signal_rate': '<20%'
    },
    'advanced_business_metrics': {
        'squeeze_avoidance_success': '>80%',
        'theme_based_trade_success': '>85%',
        'risk_reduction_measurement': 'quantified',
        'user_retention_improvement': '>10%',
        'decision_framework_adoption': '>70%'
    }
}
```

## Cost Optimization - Slice Implementation

### Slice 1A Cost Structure (Month 1-2)

| **Component**      | **Cost**          | **Justification**    |
| ------------------ | ----------------- | -------------------- |
| Polygon.io API     | $29/month         | Primary market data  |
| Local Server       | $0-200 setup      | Hardware/electricity |
| Development Time   | Focus             | Core trading value   |
| **Total Slice 1A** | **$29-229/month** | **Immediate ROI**    |

### Slice 1B Additional Costs (Month 3+)

| **Component**         | **Cost**            | **Justification**         |
| --------------------- | ------------------- | ------------------------- |
| OpenAI API            | $100-300/month      | Theme analysis            |
| Enhanced Data Sources | $200-500/month      | SEC, news, social         |
| Additional Storage    | $50-100/month       | Time-series expansion     |
| **Total Slice 1B**    | **$379-1129/month** | **Advanced intelligence** |

## Migration Strategy - Slice Evolution

### Slice 1A → Slice 1B Database Migration

```sql
-- Migration script: slice1a_to_slice1b.sql
BEGIN;

-- Add Slice 1B columns to existing tables
ALTER TABLE sector_sentiment_1a
ADD COLUMN theme_contamination JSONB DEFAULT '{}',
ADD COLUMN manipulation_risk_score DECIMAL(4,3) DEFAULT 0.0,
ADD COLUMN temperature_warning VARCHAR(20) DEFAULT 'NORMAL';

-- Create Slice 1B extension tables
\i database/slice1b_extension.sql

-- Update application version
UPDATE system_metadata
SET slice_version = '1B',
    upgrade_timestamp = NOW()
WHERE component = 'application';

COMMIT;
```

This Database & Deployment Strategy provides a comprehensive foundation for implementing the Market Sector Sentiment Analysis Tool through progressive slice enhancement, ensuring Slice 1A delivers immediate sector dashboard value while building the data architecture for Slice 1B's sophisticated theme intelligence and manipulation detection capabilities.
