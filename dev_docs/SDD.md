# Market Sector Sentiment Analysis Tool

## Software Design Document - Slice 1A Foundation & Slice 1B Framework

**Version:** 2.0 - Aligned with Slice Implementation Strategy  
**Target Markets:** NASDAQ & NYSE small-cap stocks ($10M - $2B)  
**Primary Focus:** Slice 1A - Sector sentiment "traffic light" dashboard  
**Secondary Focus:** Slice 1B - Theme detection & manipulation intelligence  
**Trading Session:** 4:00 AM - 8:00 PM ET (extended hours)  
**Development Framework:** Python FastAPI + TypeScript Next.js

## Executive Summary

The Market Sector Sentiment Analysis Tool implements a **two-slice development strategy** that delivers immediate trading value through Slice 1A while building the foundation for sophisticated manipulation detection in Slice 1B. The system targets the volatile small-cap corner of the market with **sector-first navigation** that guides traders to favorable environments before individual stock selection.

### Slice 1A: Foundation (Weeks 1-4)

- **12-slot grid** with 11 FMP sectors + 1 theme slot (PRIMARY)
- **Multi-timeframe tracking** (30min, 1D, 3D, 1W)
- **Top 3 bullish/bearish stocks per sector** with gap analysis (30% threshold)
- **1:1 FMP sector mapping** (no complex classification needed)
- **Theme slot placeholder** (future hot theme tracking)
- **Performance Target:** <1s sector grid loading, 75%+ directional accuracy

### Slice 1B: Intelligence Framework (Weeks 5-14)

- **Theme detection engine** for cross-sector narratives
- **Sympathy network analysis** for correlation-based predictions
- **Temperature monitoring** with "too hot" warnings
- **Manipulation pattern detection** for pump-and-dump identification
- **Performance Target:** 80%+ avoidance accuracy, <20% false signals

## Core Architecture Strategy

### Slice 1A Foundation Architecture

**Frontend (Next.js/TypeScript) - Foundation**

```
├── Sector Dashboard (PRIMARY) - 12-slot grid (11 FMP sectors + 1 theme)
├── Multi-timeframe Display (30min, 1D, 3D, 1W) INCREMENTAL APPROACH_ 1DAY TIMEFRAME WILL BE IMPLEMENTED FIRST. THE OTHER TIMEFRAMES WILL BE BUILT USING THE 1DAY PIPELINE AS A TEMPLATE.
├── Top Stocks Display (Top 3 bullish/bearish per sector with gap indicators)
├── Gap Analysis Indicators (Gapper boolean, Gap % display)
├── On-demand Analysis Trigger
└── Real-time Updates (30-minute intervals)
```

**Backend (FastAPI/Python) - Foundation**

```
├── Stock Universe Engine (FMP single-call approach)
├── Sector Mapping Engine (1:1 FMP → internal mapping)
├── Sector Performance Calculator (volume-weighted analysis)
├── Enhanced Stock Ranker (top 3 bullish/bearish with gap analysis)
├── Gap Analysis Engine (30% threshold calculation)
├── Color Classification Logic (5-tier sentiment system)
├── Background Analysis Scheduler (8PM, 4AM, 8AM)
└── On-demand Analysis Engine (3-5 minute full refresh)
```

**Database Layer - Foundation**

```
├── TimescaleDB (sector sentiment time-series)
├── PostgreSQL (stock universe + metadata)
├── Redis (sub-1-second caching)
└── Historical Performance (90-day retention)
```

**Configuration Layer - Foundation**

```
├── Volatility Weights Config (YAML-based, future-ready)
├── Static Weight Management (current implementation)
├── Dynamic Weight Framework (prepared for ML evolution)
└── Weight Validation & Safety Controls
```

### Slice 1B Intelligence Enhancement

**Enhanced Frontend Components**

```
├── Theme Warning Overlays (on sector cards)
├── Temperature Indicators (COLD/WARM/HOT/EXTREME)
├── Sympathy Network Visualization
├── Manipulation Risk Alerts
└── Cross-sector Contamination Display
```

**Advanced Backend Intelligence**

```
├── Theme Detection Engine (SEC filing + news analysis)
├── Cross-sector Correlation Engine (sympathy mapping)
├── Temperature Monitoring System (hourly 4AM-8PM)
├── Manipulation Pattern Recognition
└── Unified Decision Framework (theme override logic)
```

## Technology Stack - Slice Optimized

### Slice 1A Technology Requirements

- **Frontend:** Next.js 14 + React 18, TypeScript, Tailwind CSS
- **Backend:** FastAPI + Python 3.11, Pydantic validation
- **Database:** PostgreSQL 15 + TimescaleDB + Redis
- **External APIs:** FMP MCP (Ultimate tier) / Polygon.io MCP as needed if required ($29/month)
- **Configuration:** YAML-based volatility weight system, future-ready for ML
- **Gap Analysis:** FMP price data integration with 30% threshold calculation
- **Performance:** <1s sector grid, <5min on-demand analysis

### Slice 1B Additional Requirements

- **AI/ML:** OpenAI GPT-4, FinBERT sentiment analysis
- **Pattern Recognition:** scikit-learn, custom algorithms
- **Real-time Processing:** WebSocket connections, streaming analysis
- **Advanced Data:** SEC EDGAR MCP, Economic Data MCP
- **Performance:** <24hr theme detection, <100ms temperature updates

## User Workflow - Slice Evolution

### Slice 1A Primary Workflow

```
1. User opens dashboard → Sector grid loads (<1s)
2. Color-coded sectors show current sentiment (RED/BLUE/GREEN)
3. User clicks sector → Top 3 bullish/bearish stocks displayed
4. Multi-timeframe view shows 30min, 1D, 3D, 1W performance
5. On-demand refresh available (3-5 minutes)
```

### Slice 1B Enhanced Workflow

```
1. Sector grid displays with theme warnings overlays
2. Temperature indicators show momentum intensity
3. Sympathy network highlights show related movements
4. Theme alerts notify of cross-sector contamination
5. Manipulation warnings prevent pump-and-dump exposure
6. Unified recommendations combine sector + theme intelligence
```

## Small & Micro Cap Universe Strategy

### Dynamic Universe Selection Criteria

| **Criteria**     | **Micro Cap** | **Small Cap** | **Slice 1A Implementation**      |
| ---------------- | ------------- | ------------- | -------------------------------- |
| Market Cap       | $10M - $300M  | $300M - $2B   | Daily universe refresh at 8PM    |
| Min Daily Volume | 1M+ shares    | 1M+ shares    | 20-day average validation        |
| Min Price        | $2.00         | $2.00         | Penny stock exclusion            |
| Float            | >=5M shares    | >10M shares   | Shortability assessment base     |
| Exchange         | NASDAQ/NYSE   | NASDAQ/NYSE   | Regulatory oversight requirement |

**Universe Size**: Market-driven based on screening criteria only. Typically 1,500-2,500 stocks depending on market conditions, IPO activity, and delistings. No artificial size limits applied.

### Sector Category Framework

```python
# Direct 1:1 FMP Sector Mapping
FMP_SECTOR_MAPPING = {
    "Basic Materials": "basic_materials",
    "Communication Services": "communication_services",
    "Consumer Cyclical": "consumer_cyclical", 
    "Consumer Defensive": "consumer_defensive",
    "Energy": "energy",
    "Financial Services": "financial_services",
    "Healthcare": "healthcare",
    "Industrials": "industrials",
    "Real Estate": "real_estate",
    "Technology": "technology",
    "Utilities": "utilities"
}

# Theme Slot (Placeholder - Slot 12)
THEME_SLOT_PLACEHOLDER = {
    'hot_theme': {
        'name': 'User-Defined Theme',
        'description': 'Bitcoin Treasury, AI Transformation, Defense, etc.',
        'lifecycle': 'Running → Hot → Overextended → Breaking Down → Short Opportunity',
        'status': 'placeholder_concept'
    }
}

# Volatility weights for 11 FMP sectors
VOLATILITY_WEIGHTS = {
    'healthcare': 1.5,      # Highest - FDA catalysts
    'technology': 1.3,      # High - AI announcements  
    'basic_materials': 1.2, # Medium-High - Commodity driven
    'energy': 1.2,          # Medium-High - Oil/gas volatility
    'consumer_cyclical': 1.1, # Medium - Earnings sensitive
    'financial_services': 1.1, # Medium - Rate sensitive
    'communication_services': 1.0, # Neutral
    'industrials': 1.0,     # Neutral - Stable business
    'real_estate': 0.9,     # Below neutral - REIT stability
    'consumer_defensive': 0.8, # Low - Staples defensive
    'utilities': 0.7        # Lowest - Defensive sector
}
```

## Performance Calculation Strategy

### Multi-Timeframe Analysis Logic

```python
TIMEFRAME_CALCULATIONS = {
    '30min_intraday': {
        'purpose': 'Real-time sector momentum during 4AM-8PM',
        'weight': 0.4,  # High weight for immediate decisions
        'benchmark': 'Russell 2000 30min performance',
        'alert_threshold': '±3% divergence'
    },
    '1day_performance': {
        'purpose': 'Daily sector returns with after-hours',
        'weight': 0.3,  # Medium weight for trend confirmation
        'benchmark': 'Russell 2000 daily',
        'alert_threshold': '±5% divergence'
    },
    '3day_momentum': {
        'purpose': 'Short-term trend identification',
        'weight': 0.2,  # Lower weight for context
        'benchmark': 'Sector rotation analysis',
        'alert_threshold': '±10% divergence'
    },
    '1week_context': {
        'purpose': 'Medium-term cycle context',
        'weight': 0.1,  # Lowest weight for background
        'benchmark': 'Sector cycle analysis',
        'alert_threshold': '±15% divergence'
    }
}
```

### Stock Ranking Architecture

**Enhanced Stock Ranking with Gap Analysis**

The system identifies top 3 bullish and top 3 bearish stocks per sector using gap analysis to prioritize stocks with significant price movements.

**Gap Analysis Implementation:**
```python
GAP_ANALYSIS_CONFIG = {
    'threshold_percentage': 30,  # 30% gap threshold for "Gapper" classification
    'calculation_method': 'abs(current_price - previous_close) / previous_close * 100',
    'data_sources': {
        'current_price': 'FMP API price field',
        'previous_close': 'FMP API previousClose field', 
        'open_price': 'FMP API open field'
    },
    'small_cap_focus': {
        'market_cap_range': '$10M - $2B',
        'volume_requirement': '1M+ daily volume',
        'price_range': '$2.00 - $100.00'
    }
}

# Example Gap Calculation for Small-Cap Stock
# SOUN: current_price=$5.20, previous_close=$4.50, open=$4.80
# Gap % = abs(5.20 - 4.50) / 4.50 * 100 = 15.56%
# Gapper = False (below 30% threshold)
```

**Stock Ranking JSON Structure:**
```json
{
  "top_bullish_rankings": [
    {
      "symbol": "SOUN",
      "sector": "technology", 
      "current_price": 5.20,
      "previous_close": 4.50,
      "open_price": 4.80,
      "gap_percentage": 15.56,
      "gapper": false,
      "volume": 2100000,
      "market_cap": 180000000,
      "rank_reason": "Strong AI momentum, above-average volume"
    },
    {
      "symbol": "BBAI", 
      "sector": "technology",
      "current_price": 3.80,
      "previous_close": 2.90,
      "open_price": 3.10,
      "gap_percentage": 31.03,
      "gapper": true,
      "volume": 1200000,
      "market_cap": 120000000,
      "rank_reason": "Defense AI contract announcement"
    }
  ],
  "top_bearish_rankings": [
    {
      "symbol": "PRPL",
      "sector": "consumer_cyclical",
      "current_price": 4.10,
      "previous_close": 5.20,
      "open_price": 5.00,
      "gap_percentage": -21.15,
      "gapper": false,
      "volume": 1800000,
      "market_cap": 450000000,
      "rank_reason": "Earnings miss, declining volume"
    }
  ]
}
```

**Database Schema Enhancement:**
```sql
-- Add ranking columns to sector_sentiment_1d table
ALTER TABLE sector_sentiment_1d 
ADD COLUMN top_bullish_rankings TEXT,
ADD COLUMN top_bearish_rankings TEXT;

-- Create index for efficient ranking queries
CREATE INDEX idx_sector_sentiment_1d_rankings 
ON sector_sentiment_1d(sector, timestamp) 
WHERE top_bullish_rankings IS NOT NULL OR top_bearish_rankings IS NOT NULL;
```

## Slice 1B Intelligence Strategies

### Theme Detection Strategy

```python
THEME_DETECTION_FRAMEWORK = {
    'bitcoin_treasury': {
        'primary_triggers': ['8-K filings', 'treasury announcements'],
        'secondary_indicators': ['CEO statements', 'board resolutions'],
        'cross_contamination': ['mining', 'fintech', 'payments'],
        'temperature_tracking': 'hourly_during_market'
    },
    'ai_transformation': {
        'primary_triggers': ['partnership announcements', 'product launches'],
        'secondary_indicators': ['hiring patterns', 'patent filings'],
        'cross_contamination': ['healthcare', 'industrial', 'finance'],
        'temperature_tracking': 'real_time_news_flow'
    }
}
```

### Manipulation Detection Patterns

```python
MANIPULATION_PATTERNS = {
    'pump_initiation': {
        'volume_spike': '>3x average with price >15%',
        'news_quality': 'vague or promotional content',
        'insider_activity': 'Form 4 selling during pump',
        'risk_level': 'EXTREME - avoid all shorts'
    },
    'distribution_phase': {
        'volume_pattern': 'declining volume, price consolidation',
        'social_sentiment': 'retail excitement peak',
        'institutional_flow': 'smart money distribution',
        'opportunity': 'potential short entry'
    }
}
```

## Implementation Timeline & Success Metrics

### Slice 1A Success Criteria (Week 4)

- **Performance:** Sector grid loads in <1 second consistently
- **Accuracy:** 75%+ directional sector prediction (4-hour windows)
- **Reliability:** Background analysis completes within 5 minutes
- **Coverage:** 1,500+ small-cap universe maintained daily
- **User Experience:** On-demand analysis completes in 3-5 minutes
- **Configuration:** Volatility weights configurable without code changes
- **Future-Ready:** Architecture prepared for dynamic ML-based weighting

### Slice 1B Success Criteria (Week 14)

- **Theme Detection:** Identify emerging themes within 24-48 hours
- **Avoidance Accuracy:** 80%+ success avoiding momentum traps
- **Network Mapping:** 90%+ accuracy identifying sympathy relationships
- **Temperature Tracking:** Real-time status during 4AM-8PM sessions
- **Risk Reduction:** Measurable reduction in short-squeeze exposure

## Deployment Strategy - Slice Progression

### Phase 1: Local Development (Week 1)

- Environment setup with PostgreSQL + TimescaleDB + Redis
- Polygon.io MCP integration testing
- Basic sector grid implementation
- Universe filtering validation
- Volatility weight configuration system implementation

### Phase 2: Slice 1A MVP (Weeks 2-4)

- Complete 12-slot dashboard (11 FMP sectors + 1 theme placeholder)
- Multi-timeframe calculations with configurable volatility weights
- 1:1 FMP sector mapping implementation
- Background analysis scheduling
- Performance optimization (<1s grid loading)
- Theme slot placeholder UI design

### Phase 3: Local Server Deployment (Week 4+)

- Production-ready security configuration
- SSL/TLS setup and monitoring
- 1-5 beta tester deployment
- Performance validation under load

### Phase 4: Slice 1B Framework (Weeks 5-14)

- Theme detection engine implementation
- Sympathy network analysis
- Temperature monitoring system
- Manipulation pattern recognition

This Software Design Document provides a comprehensive blueprint for implementing the Market Sector Sentiment Analysis Tool through a strategic two-slice approach, delivering immediate value through Slice 1A while building the foundation for sophisticated intelligence capabilities in Slice 1B.
