# Slice 1A Development Tasks
**Focus**: 11-Sector Traffic Light Dashboard with <1s Performance  
**Target**: Dynamically calculated small-cap stock universe ($10M - $2B market cap)  
**Architecture**: FastAPI + Next.js + TimescaleDB + Redis  
**Performance Goal**: <1s sector grid loading, <5min background analysis  

---

## 📋 **CURRENT DATABASE DOCUMENTATION**

**⚠️ AUTHORITATIVE SOURCES for Current Table Structure:**
- **`backend/database/init.sql`** - Complete TimescaleDB schema (PRODUCTION TRUTH)
- **`backend/models/*.py`** - Python SQLAlchemy models (WORKING IMPLEMENTATION)

*Note: This document contains task planning and optimization strategies. For current table structures, columns, and constraints, always reference the authoritative sources above.*

---

## Development Overview

**Market Sentiment Analysis Tool - Small-Cap Sector Dashboard**

- **Version:** 1.0  
- **Target:** Small-cap sector-first sentiment analysis platform  
- **Market Cap Focus:** $10M - $2B (micro-cap to small-cap)  
- **Trading Session:** 4:00 AM - 8:00 PM ET (extended hours)  
- **Update Strategy:** Hybrid background + on-demand analysis

## 🎯 Core Objectives

Build the foundational "traffic light" sector dashboard that provides:

- **Primary:** 12-slot grid with 11 FMP sectors + 1 theme slot
- **Secondary:** Multi-timeframe performance tracking (30min, 1D, 3D, 1W)
- **Tertiary:** Top 3 bullish/bearish stocks per sector with Gap identification and Gap % 
- **Infrastructure:** 1:1 FMP sector mapping (no complex classification)
- **Theme Slot:** Placeholder for hot theme tracking

## Task Group 1: Environment Setup & Data Foundation

### Environment Setup Tasks

**Deliverables:**
- Local development environment with PostgreSQL + TimescaleDB + Redis
- Polygon.io MCP server integration and testing
- FMP MCP server setup for sector validation
- Basic FastAPI backend structure with health endpoints

**Database Setup:**
```bash
docker-compose up -d postgres redis
psql -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

**API Integration Testing:**
```bash
curl -H "Authorization: Bearer $POLYGON_API_KEY" \
  "https://api.polygon.io/v3/reference/tickers?market=stocks&active=true&limit=10"
```

**Health Endpoints to Implement:**
- `GET /health` - Overall system health
- `GET /health/database` - PostgreSQL + TimescaleDB status
- `GET /health/redis` - Redis cache status  
- `GET /health/polygon` - Polygon.io MCP connectivity

### Stock Universe Engine Tasks

**Strategic Logic: Dynamic Universe Selection**

Filter the entire market down to small-cap stocks most likely to exhibit significant gap behavior and sector-driven sentiment.

**Selection Criteria Matrix:**
| **Criteria** | **Micro Cap** | **Small Cap** | **Strategic Rationale** |
|--------------|---------------|---------------|-------------------------|
| Market Cap | $10M - $300M | $300M - $2B | Higher volatility, gap potential |
| Min Daily Volume | 1M+ shares | 1M+ shares | Liquidity for entry/exit |
| Min Price | $2.00 | $2.00 | Avoid penny stock manipulation |
| Float | >5M shares | >10M shares | Shortability assessment |
| Exchange | NASDAQ/NYSE | NASDAQ/NYSE | Regulatory oversight |

**Example Universe Selection Logic:**
```
Raw Market Data Input:
- SOUN (SoundHound AI): $180M market cap, 2.1M avg volume, $5.20 price → INCLUDE
- BBAI (BigBear.ai): $120M market cap, 950K avg volume, $3.80 price → EXCLUDE (volume)
- PRPL (Purple Innovation): $450M market cap, 1.8M avg volume, $4.10 price → INCLUDE
- KOSS (Koss Corp): $85M market cap, 3.2M avg volume, $8.90 price → INCLUDE

Universe Filtering Pipeline:
8,000+ total stocks → 3,000 market cap candidates → 2,000 liquidity filtered → 1,500 final universe
```

**Implementation Tasks:**
```python
class SmallCapUniverseSelector:
    def __init__(self, polygon_mcp):
        self.polygon_mcp = polygon_mcp
        self.market_cap_ranges = {
            'micro_cap': (10_000_000, 300_000_000),
            'small_cap': (300_000_000, 2_000_000_000)
        }
        self.min_requirements = {
            'avg_daily_volume': 1_000_000,
            'min_price': 2.00,
            'max_price': 100.00,
            'exchanges': ['NASDAQ', 'NYSE', 'NYSEARCA']
        }
    
    async def build_daily_universe(self) -> List[StockUniverse]:
        # Step 1: Get all stocks from Polygon.io
        # Step 2: Apply market cap filter
        # Step 3: Apply liquidity and price filters
        # Step 4: Validate exchange and float requirements
        # Step 5: Return clean 1,500 stock universe
```

**Deliverables:**
- Small-cap universe filtering system ($10M-$2B market cap)
- Enhanced liquidity filters (1M+ daily volume, $2-$100 price range)
- Exchange validation (NASDAQ, NYSE, NYSE American)
- Daily universe refresh with gap-prone stock prioritization

### Sector Classification System Tasks

**Strategic Logic: 1:1 FMP Sector Mapping**

**11 FMP Sectors + 1 Theme Slot Framework:**
```python
# Ultra-simple 1:1 mapping - no complex classification needed
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

# Theme Slot 12 - Placeholder Concept
THEME_SLOT_CONFIG = {
    'slot_12': {
        'purpose': 'hot_theme_tracking',
        'examples': ['Bitcoin Treasury', 'AI Transformation', 'Defense Spending'],
        'lifecycle_stages': ['Running', 'Hot', 'Overextended', 'Breaking Down', 'Short Opportunity'],
        'implementation': 'placeholder_for_future_development',
        'ui_distinction': 'different_styling_vs_sectors'
    }
}
```

**Volatility Multipliers Configuration System:**
```python
# Volatility multipliers for 11 FMP sectors + theme slot
# backend/config/volatility_weights.py
VOLATILITY_WEIGHTS = {
    'healthcare': 1.5,      # Highest - FDA catalysts
    'technology': 1.3,      # High - AI announcements
    'basic_materials': 1.2, # Medium-High - Commodity cycles
    'energy': 1.2,          # Medium-High - Oil/gas volatility
    'consumer_cyclical': 1.1, # Medium - Discretionary spending
    'financial_services': 1.1, # Medium - Interest rate sensitive
    'communication_services': 1.0, # Neutral - Mixed businesses
    'industrials': 1.0,     # Neutral - Stable operations
    'real_estate': 0.9,     # Below neutral - REIT stability
    'consumer_defensive': 0.8, # Low - Staples, necessities
    'utilities': 0.7,       # Lowest - Defensive sector
    'theme_slot': 1.5       # High - Hot themes are volatile
}
```

**Classification Decision Logic:**
```
Stock Classification Process for SOUN:
1. Primary Business: AI/Voice technology → Technology sector
2. Revenue Model: Software/licensing → Confirms technology
3. ETF Overlap: Check if held in technology ETFs → Validation
4. Volatility Profile: High-beta behavior → Assign 1.3 multiplier
5. Gap History: Frequent 10%+ gaps → Flag as high gap frequency

Result: SOUN classified as Technology, volatility multiplier 1.3
```

**Implementation Tasks:**
```python
class FMPSectorMapper:
    """Ultra-simple 1:1 FMP sector mapping - no complex classification"""
    def __init__(self):
        self.fmp_mapping = {
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
    
    def map_fmp_sector(self, fmp_sector: str) -> str:
        """Direct 1:1 mapping with 100% confidence"""
        return self.fmp_mapping.get(fmp_sector, "unknown_sector")
    
    def get_all_sectors(self) -> List[str]:
        """Return all 11 mapped sectors + theme slot placeholder"""
        sectors = list(self.fmp_mapping.values())
        sectors.append("theme_slot")  # Placeholder for slot 12
        return sectors

class ThemeSlotPlaceholder:
    """Placeholder implementation for future theme slot functionality"""
    def __init__(self):
        self.status = "placeholder"
        self.concept = {
            'slot_position': 12,
            'purpose': 'hot_theme_tracking',
            'examples': ['Bitcoin Treasury', 'AI Transformation', 'Defense'],
            'ui_design': 'different_styling_vs_regular_sectors'
        }
```

**Deliverables:**
- Ultra-simple 1:1 FMP sector mapping (no classification complexity)
- 11 FMP sectors + 1 theme slot placeholder architecture
- Configurable volatility multiplier system for all 12 slots
- Theme slot placeholder UI design and backend structure
- Clean separation: FMP data → direct mapping → internal sectors

## Task Group 2: Performance Calculation Engine

### Multi-Timeframe Analysis Tasks

**Strategic Logic: Sector Performance Calculation Framework**

The system calculates sector sentiment by aggregating individual small-cap performance within each sector, weighted by volatility and gap potential.

**Multi-Timeframe Strategy:**
```python
TIMEFRAME_ANALYSIS = {
    '30min_intraday': {
        'update_frequency': 'every_30_minutes',
        'purpose': 'capture_momentum_shifts',
        'weight_in_final_score': 0.25,
        'data_source': 'FMP_real_time'
    },
    '1day_performance': {
        'update_frequency': 'market_close_plus_after_hours',
        'purpose': 'daily_sector_rotation',
        'weight_in_final_score': 0.30,
        'data_source': 'polygon_daily_bars'
    },
    '3day_trend': {
        'update_frequency': 'daily_at_8pm',
        'purpose': 'short_term_momentum',
        'weight_in_final_score': 0.25,
        'data_source': 'polygon_historical'
    },
    '1week_context': {
        'update_frequency': 'daily_at_8pm',
        'purpose': 'sector_cycle_analysis',
        'weight_in_final_score': 0.20,
        'data_source': 'polygon_historical'
    }
}
```

**Example Sector Performance Calculation:**
```
Technology Sector Analysis (Example with SOUN, BBAI, PATH, SMCI):

Individual Stock Performance (1-day):
- SOUN: +8.2% (volume: 3.2M, 2.1x average)
- BBAI: -4.1% (volume: 1.8M, 1.9x average)  
- PATH: +12.5% (volume: 2.8M, 2.5x average)
- SMCI: -2.3% (volume: 4.1M, 1.1x average)

Weighted Calculation:
- Raw average: (+8.2 - 4.1 + 12.5 - 2.3) / 4 = +3.6%
- Volume weighting: Emphasize high-volume moves
- Volatility multiplier: 1.3x for technology sector (from config)
- Final tech sector score: +3.6% × 1.3 = +4.7%

Sentiment Classification: +4.7% = BULLISH (Green zone)
```

**Russell 2000 Benchmark Integration:**
```
Sector vs Benchmark Analysis:
- Russell 2000 (IWM) 1-day: +1.2%
- Technology sector: +4.7%
- Relative alpha: +3.5% (strong outperformance)
- Sector strength: STRONG BULLISH vs small-cap market
```

**Implementation Tasks:**
```python
class SectorPerformanceEngine:
    async def calculate_sector_performance(self, sector: str, timeframe: str) -> SectorPerformance:
        # Step 1: Get all stocks in sector from universe
        # Step 2: Fetch price/volume data for timeframe
        # Step 3: Calculate individual stock performance
        # Step 4: Apply volume weighting and configurable volatility multipliers
        # Step 5: Compare to Russell 2000 benchmark
        # Step 6: Return sector performance with relative strength
        
    async def get_multi_timeframe_analysis(self, sector: str) -> MultiTimeframeAnalysis:
        # Calculate 30min, 1D, 3D, 1W performance
        # Weight each timeframe appropriately
        # Identify momentum patterns and divergences

# Volatility multipliers now from config system
from config.volatility_weights import get_weight_for_sector
volatility_multiplier = get_weight_for_sector(sector)
```

**Deliverables:**
- 30-minute intraday: Real-time sector performance during 4 AM - 8 PM
- 1-day performance: Daily sector returns with after-hours inclusion
- 3-day performance: Short-term trend identification with momentum scoring
- 1-week performance: Medium-term sector cycle context analysis

### Color Classification Logic Tasks

**Strategic Logic: Sentiment-to-Color Decision Framework**

**Color Assignment Algorithm:**
```python
SENTIMENT_COLOR_MAPPING = {
    'dark_red': {
        'range': (-1.0, -0.6),
        'trading_signal': 'PRIME_SHORTING_ENVIRONMENT',
        'description': 'Strong bearish sentiment, multiple negative catalysts',
        'example': 'Healthcare during FDA rejection cycle'
    },
    'light_red': {
        'range': (-0.6, -0.2),
        'trading_signal': 'GOOD_SHORTING_ENVIRONMENT', 
        'description': 'Moderate bearish sentiment, some negative factors',
        'example': 'Technology during growth stock rotation'
    },
    'blue_neutral': {
        'range': (-0.2, +0.2),
        'trading_signal': 'NEUTRAL_CAUTIOUS',
        'description': 'Mixed signals, sideways action expected',
        'example': 'Energy during oil price consolidation'
    },
    'light_green': {
        'range': (+0.2, +0.6),
        'trading_signal': 'AVOID_SHORTS',
        'description': 'Moderate bullish sentiment, upward momentum',
        'example': 'Consumer during earnings beat cycle'
    },
    'dark_green': {
        'range': (+0.6, +1.0),
        'trading_signal': 'DO_NOT_SHORT',
        'description': 'Strong bullish sentiment, squeeze risk high',
        'example': 'Biotech during FDA approval announcements'
    }
}
```

**Example Color Classification Logic:**
```
Real-Time Example - Healthcare Sector Analysis:

Recent Healthcare Small-Cap Performance:
- OCUL (Ocular Therapeutix): +45% (FDA breakthrough therapy designation)
- KPTI (Karyopharm): +18% (Positive trial results)
- DTIL (Precision BioSciences): +8% (Partnership announcement)
- VRTX (Vertex): +12% (Strong earnings)

Calculation Process:
1. Raw weighted average: +20.8%
2. Healthcare volatility multiplier: 1.5x
3. Volume confirmation: High volume on all moves
4. Catalyst density: Multiple positive FDA/trial news
5. Final sentiment score: +0.85

Color Assignment: DARK GREEN (Do Not Short)
Trading Recommendation: Avoid all healthcare shorts, high squeeze risk
```

**Multi-Factor Scoring Methodology:**
```
Final Sentiment Score Calculation:
Base Performance Score: Stock price performance aggregate
× Volatility Multiplier: Sector-specific risk adjustment  
× Volume Confirmation: Higher weight for volume-supported moves
× Catalyst Density: News flow and filing frequency impact
× Technical Context: Support/resistance level consideration
= Final Sentiment Score (-1.0 to +1.0)

Example for Technology Sector:
- Base Score: +0.4 (moderate positive performance)
- Volatility Multiplier: 1.3x (tech sector adjustment)
- Volume Confirmation: 1.2x (above-average volume)
- Catalyst Density: 1.1x (moderate positive news flow)
- Technical Context: 0.9x (approaching resistance)
- Final Score: +0.4 × 1.3 × 1.2 × 1.1 × 0.9 = +0.62
- Color: DARK GREEN (Do Not Short)
```

**Implementation Tasks:**
```python
class ColorClassificationEngine:
    def calculate_sentiment_score(self, sector_performance: SectorPerformance) -> float:
        # Apply multi-factor scoring methodology
        # Include volume confirmation and catalyst density
        # Return score between -1.0 and +1.0
        
    def assign_color_classification(self, sentiment_score: float) -> ColorClassification:
        # Map sentiment score to color categories
        # Include trading signal and risk assessment
        # Return color with confidence level
```

**Deliverables:**
- Sentiment scoring algorithm (-1.0 to +1.0 scale) with multi-factor weighting
- 5-color classification system with clear trading signals
- Volume confirmation integration for score validation
- Catalyst density analysis for sentiment strength assessment

### Data Persistence & Caching Tasks

**Strategic Logic: Performance-Optimized Data Architecture**

**Data Storage Strategy:**
```python
PERFORMANCE_OPTIMIZATION_STRATEGY = {
    'real_time_cache': {
        'technology': 'Redis',
        'purpose': 'Sub-1-second sector grid loading',
        'data_types': ['current_sentiment_scores', 'color_assignments', 'top_stocks'],
        'ttl': '30_minutes_during_market_hours'
    },
    'time_series_storage': {
        'technology': 'TimescaleDB',
        'purpose': 'Historical pattern analysis and backtesting',
        'retention': '90_days_full_detail',
        'compression': 'after_7_days'
    },
    'calculation_cache': {
        'technology': 'PostgreSQL',
        'purpose': 'Intermediate calculation storage',
        'refresh_frequency': 'background_analysis_cycles'
    }
}
```

**Cache Optimization for Small-Cap Universe:**
```
Cache Hit Strategy Example:
User requests Technology sector at 2:47 PM:
1. Check Redis cache for tech_sector_sentiment_2_30pm
2. If hit: Return cached data (response time: <100ms)
3. If miss: Calculate fresh (response time: 2-3 seconds)
4. Store in cache for next 30 minutes
5. Serve to user with freshness timestamp

Small-Cap Specific Optimizations:
- Pre-calculate universe daily at 8 PM
- Cache top 3 bullish/bearish per sector
- Maintain rolling 7-day performance history
- Optimize for 1,500 stock universe size
```

**Database Schema Tasks:**
```sql
-- TimescaleDB Schema
CREATE TABLE sector_sentiment (
    timestamp TIMESTAMPTZ NOT NULL,
    sector VARCHAR(50) NOT NULL,
    sentiment_score DECIMAL(4,3),
    color_classification VARCHAR(20),
    confidence_level DECIMAL(3,2),
    PRIMARY KEY (timestamp, sector)
);

SELECT create_hypertable('sector_sentiment', 'timestamp');

-- Stock Universe Table
CREATE TABLE stock_universe (
    symbol VARCHAR(10) PRIMARY KEY,
    market_cap BIGINT,
    avg_daily_volume BIGINT,
    sector VARCHAR(50),
    volatility_multiplier DECIMAL(3,1),
    last_updated TIMESTAMPTZ
);

-- Redis Cache Structure
sector:{sector_name}:sentiment -> JSON with current sentiment data
sector:{sector_name}:top_stocks -> JSON with top 3 bullish/bearish
universe:stocks -> Set of all tracked stock symbols
```

**Deliverables:**
- TimescaleDB time-series implementation for sector sentiment history
- Redis caching layer for sub-1-second sector grid performance
- 90-day historical retention for pattern analysis and backtesting
- Data integrity validation and error handling systems

## Task Group 3: Analysis Scheduling System

### Hybrid Analysis Engine Tasks

**Strategic Logic: Flexible Analysis Timing Framework**

**Option 2 Hybrid Analysis Strategy:**
The system provides both automated background analysis and user-triggered on-demand analysis to accommodate different trader schedules and preferences.

**Background Analysis Schedule:**
```python
AUTOMATED_ANALYSIS_SCHEDULE = {
    '8:00_PM_ET': {
        'trigger': 'post_extended_hours_close',
        'purpose': 'comprehensive_daily_analysis',
        'scope': 'full_universe_multi_timeframe',
        'completion_time': '5_minutes',
        'next_day_prep': 'cache_results_for_morning_access'
    },
    '4:00_AM_ET': {
        'trigger': 'pre_market_preparation',
        'purpose': 'overnight_impact_analysis',
        'scope': 'sector_sentiment_updates',
        'completion_time': '3_minutes',
        'focus': 'international_market_impact'
    },
    '8:00_AM_ET': {
        'trigger': 'final_pre_market_check',
        'purpose': 'economic_data_integration',
        'scope': 'final_sentiment_adjustments',
        'completion_time': '2_minutes',
        'focus': '8:30_AM_economic_releases'
    }
}
```

**On-Demand Analysis Logic:**
```
User-Triggered Analysis Decision Tree:

User sits down at 6:37 AM:
1. Check last analysis timestamp: 4:00 AM (2 hours 37 minutes ago)
2. Evaluate freshness tolerance: <2 hours = fresh, >2 hours = stale
3. Display options:
   - "View 4:00 AM Analysis" (instant access)
   - "Run Fresh Analysis" (3-5 minute wait)
4. Smart recommendation: "4 AM analysis available, refresh recommended if major overnight news"
```

**Implementation Tasks:**
```python
class HybridAnalysisEngine:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.analysis_cache = AnalysisCache()
        
    async def schedule_background_analysis(self):
        # Schedule 8 PM, 4 AM, 8 AM analysis
        # Handle timezone conversions properly
        # Implement error handling and retries
        
    async def run_on_demand_analysis(self, user_id: str) -> AnalysisResult:
        # Check cache freshness
        # Provide user with options
        # Run fresh analysis if requested
        # Update cache with new results
        
    async def smart_cache_strategy(self, timestamp: datetime) -> CacheStrategy:
        # If analysis <2 hours old: Serve instantly
        # If analysis 2-4 hours old: Serve + offer refresh
        # If analysis >4 hours old: Recommend fresh
```

**Deliverables:**
- Background analysis scheduler with 8 PM/4 AM/8 AM automation
- On-demand analysis system with 3-5 minute completion time
- Smart caching with freshness-based recommendations
- User preference system for analysis timing customization

### Stock Ranking System Tasks

**Strategic Logic: Top Stock Identification Framework**

**Ranking Algorithm for Top 3 Selection:**
```python
STOCK_RANKING_CRITERIA = {
    'gap_magnitude': {
        'weight': 0.40,
        'calculation': 'abs(current_price - previous_close) / previous_close',
        'small_cap_example': 'SOUN +12% gap = high ranking'
    },
    'volume_confirmation': {
        'weight': 0.30,
        'calculation': 'current_volume / 20_day_average_volume',
        'small_cap_example': 'BBAI 2.5x volume = strong confirmation'
    },
    'sector_alignment': {
        'weight': 0.20,
        'calculation': 'stock_direction_matches_sector_sentiment',
        'small_cap_example': 'PRPL down in bearish consumer = alignment bonus'
    },
    'shortability_preview': {
        'weight': 0.10,
        'calculation': 'basic_float_and_liquidity_score',
        'small_cap_example': 'KOSS high float = better shortability'
    }
}
```

**Example Top 3 Selection Process:**
```
Technology Sector Ranking Example (Bearish Scenario):

Available Candidates:
- SOUN: -8.2% gap, 2.1x volume, bearish alignment, good float → Score: 8.3
- BBAI: -6.1% gap, 3.2x volume, bearish alignment, poor float → Score: 7.8  
- PATH: -4.5% gap, 1.8x volume, bearish alignment, good float → Score: 7.1
- SMCI: -12.1% gap, 1.2x volume, bearish alignment, excellent float → Score: 8.7

Top 3 Bearish Selection:
1. SMCI: 8.7 (largest gap + excellent shortability)
2. SOUN: 8.3 (strong gap + volume confirmation)  
3. BBAI: 7.8 (highest volume confirmation despite float issues)

Result Display:
📉 TOP BEARISH: SMCI -12.1%, SOUN -8.2%, BBAI -6.1%
```

**Implementation Tasks:**
```python
class StockRankingEngine:
    def calculate_ranking_score(self, stock: StockData, sector_sentiment: SectorSentiment) -> float:
        # Apply multi-factor ranking criteria
        # Weight by gap magnitude, volume, alignment, shortability
        # Return composite score 0-10
        
    def select_top_stocks(self, sector: str, sentiment_direction: str) -> TopStocks:
        # Get all stocks in sector
        # Calculate ranking scores
        # Select top 3 bullish and top 3 bearish
        # Handle mixed signal scenarios
```

**Deliverables:**
- Multi-factor ranking algorithm with small-cap optimization
- Top 3 bullish/bearish selection per sector with real-time updates
- Volume confirmation and shortability integration
- Dynamic re-ranking on significant price movements

### Stock Ranking & Gap Analysis Tasks

**Strategic Logic: Enhanced Stock Ranking with Gap Analysis**

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

**Enhanced Stock Ranking JSON Structure:**
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

**Database Schema Updates:**
```sql
-- Add ranking columns to sector_sentiment_1d table
ALTER TABLE sector_sentiment_1d 
ADD COLUMN top_bullish_rankings TEXT,
ADD COLUMN top_bearish_rankings TEXT;

-- Create index for efficient ranking queries
CREATE INDEX idx_sector_sentiment_1d_rankings 
ON sector_sentiment_1d(sector, timestamp) 
WHERE top_bullish_rankings IS NOT NULL OR top_bearish_rankings IS NOT NULL;

-- Add trigger to validate small-cap universe
CREATE OR REPLACE FUNCTION validate_small_cap_universe()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure only small-cap stocks are included in rankings
    -- Market cap validation logic here
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_small_cap_universe
    BEFORE INSERT OR UPDATE ON sector_sentiment_1d
    FOR EACH ROW EXECUTE FUNCTION validate_small_cap_universe();
```

**Gap Analysis Engine Implementation:**
```python
class GapAnalysisEngine:
    def __init__(self, threshold_percentage: int = 30):
        self.threshold_percentage = threshold_percentage
        
    def calculate_gap_percentage(self, current_price: float, previous_close: float) -> float:
        """Calculate gap percentage using FMP data"""
        if previous_close == 0:
            return 0.0
        return abs(current_price - previous_close) / previous_close * 100
        
    def is_gapper(self, gap_percentage: float) -> bool:
        """Determine if stock meets gapper threshold"""
        return gap_percentage >= self.threshold_percentage
        
    def analyze_stock_gap(self, stock_data: dict) -> dict:
        """Complete gap analysis for a stock"""
        gap_percentage = self.calculate_gap_percentage(
            stock_data['current_price'], 
            stock_data['previous_close']
        )
        return {
            'symbol': stock_data['symbol'],
            'gap_percentage': gap_percentage,
            'gapper': self.is_gapper(gap_percentage),
            'current_price': stock_data['current_price'],
            'previous_close': stock_data['previous_close'],
            'open_price': stock_data['open_price']
        }
```

**Enhanced Stock Ranker Implementation:**
```python
class EnhancedStockRanker:
    def __init__(self, gap_engine: GapAnalysisEngine):
        self.gap_engine = gap_engine
        
    def rank_stocks_by_sector(self, sector_stocks: List[dict], sector_sentiment: str) -> dict:
        """Rank stocks within a sector for bullish/bearish selection"""
        # Apply gap analysis to all stocks
        analyzed_stocks = [
            {**stock, **self.gap_engine.analyze_stock_gap(stock)}
            for stock in sector_stocks
        ]
        
        # Filter for small-cap stocks only
        small_cap_stocks = [
            stock for stock in analyzed_stocks
            if 10_000_000 <= stock['market_cap'] <= 2_000_000_000
        ]
        
        # Rank by gap percentage and other criteria
        bullish_candidates = [
            stock for stock in small_cap_stocks
            if stock['gap_percentage'] > 0  # Positive gap
        ]
        bearish_candidates = [
            stock for stock in small_cap_stocks
            if stock['gap_percentage'] < 0  # Negative gap
        ]
        
        # Select top 3 for each direction
        top_bullish = sorted(bullish_candidates, 
                           key=lambda x: x['gap_percentage'], reverse=True)[:3]
        top_bearish = sorted(bearish_candidates, 
                           key=lambda x: abs(x['gap_percentage']), reverse=True)[:3]
        
        return {
            'top_bullish_rankings': top_bullish,
            'top_bearish_rankings': top_bearish
        }
```

**Implementation Tasks:**
```python
# 1. Create GapAnalysisEngine class
# 2. Enhance StockRanker with gap analysis integration
# 3. Update sector_sentiment_1d model with ranking columns
# 4. Implement database schema updates
# 5. Add small-cap validation triggers
# 6. Update API responses to include ranking data
# 7. Test with real FMP data for accuracy
```

**Deliverables:**
- Gap analysis engine with 30% threshold calculation
- Enhanced stock ranker with small-cap filtering
- Database schema updates for ranking storage
- JSON structure for top 3 bullish/bearish rankings
- Small-cap universe validation triggers
- Integration with existing sector calculation pipeline

### Performance Optimization Tasks

**Strategic Logic: Speed and Reliability Framework**

**Performance Optimization Strategy:**
```python
SPEED_OPTIMIZATION_TARGETS = {
    'sector_grid_load': {
        'target': '<1_second',
        'method': 'redis_cache_pre_calculation',
        'fallback': 'graceful_degradation_to_2_seconds'
    },
    'on_demand_analysis': {
        'target': '3-5_minutes_complete_universe',
        'method': 'parallel_processing_by_sector',
        'progress_indicator': 'real_time_completion_percentage'
    },
    'individual_stock_lookup': {
        'target': '<2_seconds',
        'method': 'pre_calculated_universe_cache',
        'scope': '1500_stock_universe'
    },
    'real_time_updates': {
        'target': '<500ms_websocket_latency',
        'method': 'optimized_change_detection',
        'frequency': 'every_30_minutes_or_significant_moves'
    }
}
```

**Implementation Tasks:**
```python
class PerformanceOptimizer:
    async def optimize_database_queries(self):
        # Create indexes for common query patterns
        # Implement connection pooling
        # Add query caching for repeated requests
        
    async def implement_graceful_degradation(self):
        # API failure fallback strategies
        # Performance degradation handling
        # User experience maintenance during issues
        
    async def setup_monitoring(self):
        # Response time tracking
        # Error rate monitoring
        # Resource usage alerts
```

**Deliverables:**
- Sub-1-second sector grid loading with Redis optimization
- 3-5 minute on-demand analysis with progress tracking
- <500ms WebSocket latency for real-time updates
- Comprehensive error handling and graceful degradation system

## Task Group 4: User Interface & Integration

### Sector Dashboard UI Tasks

**Strategic Logic: Trader-Focused Interface Design**

Small-cap intraday traders typically use multi-monitor setups and need information density over visual aesthetics. The interface prioritizes actionable intelligence and rapid decision-making.

**Individual Sector Card Design Framework:**
```
Sector Card Information Hierarchy:

TECHNOLOGY SECTOR 🔴 BEARISH -0.73
┌──────────────────────────────────────────┐
│ Multi-Timeframe Indicators:              │
│ 30M: 🔴 -0.8  1D: 🔴 -2.4               │
│ 3D:  🔴 -5.1  1W: 🔵 +1.2               │
├──────────────────────────────────────────┤
│ 📉 TOP BEARISH (Shortable):              │
│ • SOUN -8.2% (2.1x vol)                  │
│ • BBAI -6.1% (3.2x vol)                  │  
│ • PATH -4.5% (1.8x vol)                  │
├──────────────────────────────────────────┤
│ 📈 TOP BULLISH:                          │
│ • None in bearish sector                 │
│ • Wait for sector reversal               │
└──────────────────────────────────────────┘

Visual Design Principles:
- Color dominates: Sector sentiment immediately visible
- Numbers secondary: Specific percentages support the color signal
- Actionable focus: Emphasize tradeable opportunities
- Context provided: Multi-timeframe prevents single-period bias
```

**Real-World Small-Cap Sector Display Examples:**
```
Healthcare Sector (Bullish Example):
HEALTHCARE 🟢 BULLISH +0.58
30M: 🟢 +0.6  1D: 🟢 +1.2  3D: 🟢 +2.1  1W: 🟢 +3.5
📈 TOP BULLISH: OCUL +45% (FDA), KPTI +18% (Trial), DTIL +8% (Partner)
📉 TOP BEARISH: None (avoid shorts in bullish sector)

Consumer Sector (Mixed Example):  
CONSUMER 🟡 CAUTION +0.23
30M: 🟡 +0.3  1D: 🟡 +0.8  3D: 🟢 +1.5  1W: 🟢 +2.1
📈 TOP BULLISH: PRPL +5% (Earnings), EXPR +3% (Guidance)
📉 TOP BEARISH: GME -2% (Offering), AMC -1% (Dilution)

Energy Sector (Neutral Example):
ENERGY 🔵 NEUTRAL +0.12  
30M: 🔵 +0.1  1D: 🔵 +0.0  3D: 🔵 -0.2  1W: 🔵 -0.5
📈 TOP BULLISH: GREE +3% (Mining), HIVE +2% (Bitcoin)
📉 TOP BEARISH: BTCS -1% (Profit), SID -2% (Steel)
```

**Implementation Tasks:**
```typescript
// React Components for Sector Dashboard
interface SectorCardProps {
  sector: SectorData;
  timeframes: TimeframeData[];
  topStocks: TopStocks;
  onClick: () => void;
}

const SectorCard: React.FC<SectorCardProps> = ({ sector, timeframes, topStocks }) => {
  return (
    <div className={`sector-card ${getSectorColorClass(sector.sentiment)}`}>
      <SectorHeader sector={sector} />
      <TimeframeIndicators timeframes={timeframes} />
      <TopStocksList stocks={topStocks} />
    </div>
  );
};

// CSS Classes for Color Coding
.sector-card.dark-red { background: linear-gradient(135deg, #dc2626, #b91c1c); }
.sector-card.light-red { background: linear-gradient(135deg, #ef4444, #dc2626); }
.sector-card.blue-neutral { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.sector-card.light-green { background: linear-gradient(135deg, #10b981, #059669); }
.sector-card.dark-green { background: linear-gradient(135deg, #059669, #047857); }
```

**Deliverables:**
- Responsive sector grid (4 per row desktop, 2 per row tablet)
- Color-coded sector cards with immediate sentiment recognition
- Multi-timeframe indicators (30min/1D/3D/1W) per sector card
- Top 3 bullish/bearish stock display with volume confirmation

### Real-Time Updates Tasks

**Strategic Logic: Live Data Integration Framework**

**WebSocket Update Strategy:**
```python
REAL_TIME_UPDATE_FRAMEWORK = {
    'sector_sentiment_updates': {
        'frequency': 'every_30_minutes',
        'trigger': 'background_calculation_completion',
        'payload': 'sector_scores_and_colors_only',
        'latency_target': '<100ms'
    },
    'significant_move_alerts': {
        'frequency': 'immediate',
        'trigger': 'stock_move_greater_than_15_percent',
        'payload': 'affected_sector_recalculation',
        'example': 'SOUN -20% triggers Tech sector update'
    },
    'top_stock_changes': {
        'frequency': 'on_ranking_change',
        'trigger': 'top_3_list_modification',
        'payload': 'new_rankings_per_sector',
        'example': 'BBAI enters top 3 bearish in Technology'
    }
}
```

**Change Detection and User Notifications:**
```
Visual Update Strategy:

Sector Color Changes:
- Fade effect when transitioning between colors
- Brief highlight border to draw attention to change
- Timestamp of last update displayed
- Previous color shown briefly for context

Stock List Updates:
- Smooth animation when stocks enter/exit top 3
- Price change highlighting (green up, red down)
- Volume spike indicators (bolded volume ratios)
- New entry alerts ("NEW" badge for first-time appearances)

Connection Status Management:
- Live connection indicator (green dot = connected)
- Reconnection attempts with user visibility
- Graceful fallback to last known data during outages
- Manual refresh capability if WebSocket fails
```

**Implementation Tasks:**
```python
class WebSocketManager:
    async def setup_websocket_server(self):
        # Configure WebSocket server for real-time updates
        # Handle multiple client connections
        # Implement message queuing for reliability
        
    async def broadcast_sector_updates(self, sector_data: SectorUpdate):
        # Send sector sentiment changes to all connected clients
        # Include only necessary data to minimize bandwidth
        # Handle connection failures gracefully
        
    async def handle_significant_moves(self, stock_move: StockMove):
        # Detect 15%+ moves in tracked universe
        # Trigger sector recalculation if needed
        # Broadcast immediate updates to affected sectors
```

**Deliverables:**
- WebSocket real-time update system with <100ms latency
- Visual change detection with smooth transition animations
- Automatic reconnection and error handling
- Manual refresh capability and connection status monitoring

### Testing & Deployment Tasks

**Strategic Logic: Production Readiness Validation**

**Comprehensive Testing Strategy:**
```python
TESTING_FRAMEWORK = {
    'unit_tests': {
        'coverage_target': '90_percent',
        'focus_areas': [
            'sector_sentiment_calculations',
            'color_classification_logic', 
            'stock_ranking_algorithms',
            'cache_invalidation_rules'
        ],
        'small_cap_test_data': 'SOUN_BBAI_OCUL_KPTI_sample_scenarios'
    },
    'integration_tests': {
        'mcp_server_connections': 'polygon_and_fmp_reliability',
        'database_operations': 'timescaledb_and_redis_performance',
        'websocket_functionality': 'real_time_update_delivery',
        'analysis_pipeline': 'end_to_end_8pm_analysis_validation'
    },
    'load_tests': {
        'concurrent_users': '5_simultaneous_connections',
        'analysis_performance': 'on_demand_analysis_under_load',
        'database_stress': '1500_stock_universe_query_speed',
        'memory_usage': 'sustained_operation_monitoring'
    }
}
```

**Small-Cap Specific Validation:**
```
Universe Validation Tests:

Market Cap Filtering:
- Verify SOUN ($180M) included, large caps excluded
- Confirm micro-caps like KOSS ($85M) properly included
- Test boundary conditions around $10M and $2B limits

Liquidity Filtering:
- Validate 1M+ volume requirement correctly applied
- Test that BBAI with 950K volume gets excluded
- Confirm volume calculations use 20-day average

Sector Classification:
- Verify SOUN correctly assigned to Technology sector
- Confirm OCUL properly classified as Healthcare
- Test edge cases where sector assignment is ambiguous

Performance Calculations:
- Test healthcare sector with OCUL +45% FDA move
- Validate technology sector with mixed SOUN/BBAI performance  
- Confirm volume weighting properly emphasizes high-volume moves

Real-World Scenario Testing:
- Simulate FDA approval announcement impact on biotech sector
- Test sector rotation scenario (tech selloff, healthcare strength)
- Validate gap detection for 15%+ overnight moves
```

**Deployment Configuration:**
```yaml
# Docker Compose Configuration
version: '3.8'
services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: market_sentiment
      POSTGRES_USER: sentiment_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
      
  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://sentiment_user:${DB_PASSWORD}@postgres:5432/market_sentiment
      REDIS_URL: redis://redis:6379
      POLYGON_API_KEY: ${POLYGON_API_KEY}
      FMP_API_KEY: ${FMP_API_KEY}
    depends_on:
      - postgres
      - redis
      
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

**Deliverables:**
- Comprehensive test suite with 90%+ coverage
- Load testing validation for 5+ concurrent users
- Production deployment configuration with security hardening
- Performance monitoring and health check system

## 📊 Success Metrics & Validation

### Performance Criteria
- **Sector Grid Load Time:** <1 second consistently
- **On-Demand Analysis:** 3-5 minute completion for full universe
- **WebSocket Latency:** <500ms for real-time updates
- **Database Queries:** <500ms average response time
- **Memory Usage:** Stable operation over 24-hour periods

### Accuracy Targets
- **Universe Coverage:** 1,500+ small-cap stocks maintained daily
- **Sector Classification:** 95%+ accuracy validated manually
- **Directional Prediction:** 75%+ sector sentiment accuracy (4-hour windows)
- **Color Assignment:** <1 second refresh time for sentiment changes
- **Gap Detection:** <30 seconds from market open for significant moves

### System Reliability
- **Uptime:** 99.5% during market hours (4 AM - 8 PM ET)
- **Error Rate:** <1% for critical user flows
- **API Connectivity:** Graceful degradation for external API failures
- **Cache Hit Rate:** >90% for frequently accessed sector data
- **Background Analysis:** 100% completion rate for scheduled runs

### User Experience
- **Analysis Freshness:** Clear indicators of data age and reliability
- **Visual Responsiveness:** Smooth color transitions and animations
- **Error Handling:** Clear messaging for any system issues
- **Mobile Compatibility:** Functional on tablet devices (768px+)
- **Information Density:** Actionable data without overwhelming interface