# Market Sentiment Analysis Tool
## Implementation Plan: Slice 1A Foundation & Slice 1B Framework

**Version:** 1.0  
**Target:** Small-cap sector-first sentiment analysis platform  
**Market Cap Focus:** $10M - $2B (micro-cap to small-cap)  
**Trading Session:** 4:00 AM - 8:00 PM ET (extended hours)  
**Update Strategy:** Option 2 - Hybrid background + on-demand analysis

---

## 🎯 SLICE 1A: Foundation Implementation Plan

### Overview
Build the core "traffic light" sector dashboard that provides real-time sector sentiment with background analysis scheduling and on-demand refresh capabilities.

### Core Objectives
- **Primary:** 12-slot grid with 11 FMP sectors + 1 theme slot
- **Secondary:** Multi-timeframe performance tracking (30min, 1D, 3D, 1W)
- **Tertiary:** Top 3 bullish/bearish stocks per sector
- **Infrastructure:** 1:1 FMP sector mapping (ultra-simple approach)
- **Theme Slot:** Placeholder for hot theme tracking (Bitcoin Treasury, AI, etc.)

---

### Week 1: Data Foundation & Universe Building

#### Day 1-2: Environment Setup
**Deliverables:**
- Local development environment with PostgreSQL + TimescaleDB + Redis
- Polygon.io MCP server integration and testing
- FMP MCP server setup for sector validation
- Basic FastAPI backend structure with health endpoints

**Technical Focus:**
- Database schema implementation for time-series sector data
- API key management and secure configuration
- Basic error handling and logging setup

#### Day 3-5: Stock Universe Engine

**Strategic Logic: Dynamic Universe Selection**

**Core Universe Selection Strategy:**
The goal is to filter the entire market down to small-cap stocks most likely to exhibit significant gap behavior and sector-driven sentiment.

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

**Micro Cap Enhanced Filtering Strategy:**
- **Stricter liquidity requirements** for micro caps (1M+ vs traditional 500K)
- **Float analysis** to ensure actual shortability potential
- **SEC filing frequency** to avoid shells and dormant companies
- **Recent trading activity** validation (active within 30 days)

**Deliverables:**
- Small-cap universe filtering system ($10M-$2B market cap)
- Enhanced liquidity filters (1M+ daily volume, $2-$100 price range)
- Exchange validation (NASDAQ, NYSE, NYSE American)
- Daily universe refresh with gap-prone stock prioritization

#### Day 6-7: Sector Classification System

**Strategic Logic: 1:1 FMP Sector Mapping**

**11 FMP Sectors + 1 Theme Slot Framework:**
```
SECTOR_MAPPING = {
    'technology': {
        'etf_proxy': 'XLK',
        'small_cap_examples': ['SOUN', 'BBAI', 'PATH', 'SMCI'],
        'volatility_multiplier': 1.3,  # Higher vol weighting
        'gap_frequency': 'high'         # Frequent gap behavior
    },
    'healthcare': {
        'etf_proxy': 'XLV', 
        'small_cap_examples': ['OCUL', 'KPTI', 'DTIL', 'VRTX'],
        'volatility_multiplier': 1.5,  # Highest due to FDA catalysts
        'gap_frequency': 'extreme'      # FDA news creates massive gaps
    },
    'energy': {
        'etf_proxy': 'XLE',
        'small_cap_examples': ['GREE', 'HIVE', 'BTCS', 'SID'],
        'volatility_multiplier': 1.2,
        'gap_frequency': 'moderate'     # Commodity driven
    },
    'financial': {
        'etf_proxy': 'XLF',
        'small_cap_examples': ['SOFI', 'UPST', 'AFRM', 'LC'],
        'volatility_multiplier': 1.1,
        'gap_frequency': 'moderate'     # Regulatory sensitive
    },
    'consumer_discretionary': {
        'etf_proxy': 'XLY',
        'small_cap_examples': ['PRPL', 'EXPR', 'GME', 'AMC'],
        'volatility_multiplier': 1.2,
        'gap_frequency': 'high'         # Meme stock potential
    },
    'industrials': {
        'etf_proxy': 'XLI',
        'small_cap_examples': ['BLDE', 'STRL', 'PTRA', 'FSR'],
        'volatility_multiplier': 1.0,
        'gap_frequency': 'low'          # More stable
    },
    'materials': {
        'etf_proxy': 'XLB',
        'small_cap_examples': ['TLOFF', 'SID', 'SCCO', 'FCX'],
        'volatility_multiplier': 0.9,
        'gap_frequency': 'low'          # Commodity cycles
    },
    'utilities': {
        'etf_proxy': 'XLU',
        'small_cap_examples': ['NOVA', 'CWEN', 'BEPC', 'NEP'],
        'volatility_multiplier': 0.7,
        'gap_frequency': 'very_low'     # Defensive sector
    }
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

**Deliverables:**
- Ultra-simple 1:1 FMP sector mapping (11 sectors)
- Theme slot placeholder architecture (slot 12)
- Volatility multiplier assignment for all 12 slots
- UI layout design for 12-slot grid (4x3 or 3x4)

---

### Week 2: Performance Calculation Engine

#### Day 8-10: Multi-Timeframe Analysis

**Strategic Logic: Sector Performance Calculation Framework**

**Performance Calculation Methodology:**
The system calculates sector sentiment by aggregating individual small-cap performance within each sector, weighted by volatility and gap potential.

**Multi-Timeframe Strategy:**
```
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
- Volatility multiplier: 1.3x for technology sector
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

**Deliverables:**
- **30-minute intraday:** Real-time sector performance during 4 AM - 8 PM
- **1-day performance:** Daily sector returns with after-hours inclusion
- **3-day performance:** Short-term trend identification with momentum scoring
- **1-week performance:** Medium-term sector cycle context analysis

#### Day 11-12: Color Classification Logic

**Strategic Logic: Sentiment-to-Color Decision Framework**

**Color Assignment Algorithm:**
```
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

Sector Card Display:
[HEALTHCARE 🟢] DO NOT SHORT
+20.8% | Multiple FDA catalysts active
📈 BULLISH: OCUL +45%, KPTI +18%, DTIL +8%
⚠️ SQUEEZE RISK: Avoid shorts until momentum cools
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

**Deliverables:**
- Sentiment scoring algorithm (-1.0 to +1.0 scale) with multi-factor weighting
- 5-color classification system with clear trading signals
- Volume confirmation integration for score validation
- Catalyst density analysis for sentiment strength assessment

#### Day 13-14: Data Persistence & Caching

**Strategic Logic: Performance-Optimized Data Architecture**

**Data Storage Strategy:**
```
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

**Deliverables:**
- TimescaleDB time-series implementation for sector sentiment history
- Redis caching layer for sub-1-second sector grid performance
- 90-day historical retention for pattern analysis and backtesting
- Data integrity validation and error handling systems

---

### Week 3: Analysis Scheduling System

#### Day 15-17: Hybrid Analysis Engine

**Strategic Logic: Flexible Analysis Timing Framework**

**Option 2 Hybrid Analysis Strategy:**
The system provides both automated background analysis and user-triggered on-demand analysis to accommodate different trader schedules and preferences.

**Background Analysis Schedule:**
```
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

On-Demand Analysis Triggers:
- User clicks "Refresh Analysis" button
- Major market event detected (VIX spike >5%)
- Unusual pre-market volume in tracked universe
- Economic data release with >0.5% market impact
```

**Example Analysis Scenarios:**
```
Scenario 1: Early Bird Trader (3:30 AM)
- Last background analysis: 8:00 PM previous day (7.5 hours old)
- Recommendation: "Analysis from 8 PM available, refresh recommended for overnight news"
- Action: Show cached 8 PM results + "Refresh" button for current analysis

Scenario 2: Standard Prep Trader (7:00 AM)  
- Last background analysis: 4:00 AM (3 hours ago)
- Status: "4 AM analysis available (captures overnight moves)"
- Action: Display 4 AM results with freshness indicator
- Option: Manual refresh for latest pre-market activity

Scenario 3: Just-in-Time Trader (9:15 AM)
- Last background analysis: 8:00 AM (1 hour 15 minutes ago)
- Status: "8 AM analysis current (post-economic data)"
- Action: Display current results
- Option: Ultra-fresh analysis if desired before market open
```

**Smart Caching Strategy:**
```
Cache Intelligence System:
- If analysis <2 hours old: Serve instantly from cache
- If analysis 2-4 hours old: Serve cache + offer refresh
- If analysis >4 hours old: Recommend fresh analysis
- If major catalyst detected: Auto-suggest refresh regardless of timing

Small-Cap Specific Optimizations:
- Pre-calculate top 3 bullish/bearish per sector
- Cache sector ETF performance for benchmarking
- Store gap candidates from universe screening
- Maintain rolling performance metrics for quick access
```

**Deliverables:**
- Background analysis scheduler with 8 PM/4 AM/8 AM automation
- On-demand analysis system with 3-5 minute completion time
- Smart caching with freshness-based recommendations
- User preference system for analysis timing customization

#### Day 18-19: Stock Ranking System

**Strategic Logic: Top Stock Identification Framework**

**Ranking Algorithm for Top 3 Selection:**
```
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
Technology Sector Ranking Example (Bearish Day):

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

**Bullish vs Bearish Selection Logic:**
```
Bullish Stock Selection (Green/Light Green Sectors):
- Prioritize momentum plays with volume
- Focus on breakout patterns and gap-ups  
- Emphasize sector leadership and relative strength
- Example: "OCUL +15% on FDA news, KPTI +8% sympathy"

Bearish Stock Selection (Red/Dark Red Sectors):
- Prioritize shortable candidates with high float
- Focus on gap-downs with volume confirmation
- Emphasize technical breakdown patterns
- Example: "EXPR -12% earnings miss, PRPL -8% guidance cut"

Mixed Sector Handling (Blue/Neutral):
- Show both sides but with lower conviction
- Indicate mixed signals in display
- Focus on highest conviction individual setups
- Example: "Mixed signals: GREE +6%, HIVE -4%"
```

**Real-Time Updates Strategy:**
```
Stock Pick Refresh Logic:
- Update every 30 minutes during market hours (4 AM - 8 PM)
- Immediate update on 15%+ moves in tracked universe
- Recalculate on major sector sentiment shifts (>0.3 change)
- Background validation of shortability status

Update Trigger Example:
10:47 AM: SOUN suddenly drops -15% on news
→ Immediate recalculation triggered
→ SOUN moves to #1 bearish in Technology 
→ Push update to all connected users
→ Cache new rankings for 30-minute cycle
```

**Deliverables:**
- Multi-factor ranking algorithm with small-cap optimization
- Top 3 bullish/bearish selection per sector with real-time updates
- Volume confirmation and shortability integration
- Dynamic re-ranking on significant price movements

#### Day 20-21: Performance Optimization

**Strategic Logic: Speed and Reliability Framework**

**Performance Optimization Strategy:**
```
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

**Small-Cap Universe Optimization:**
```
1,500 Stock Universe Performance Strategy:

Database Query Optimization:
- Pre-calculate sector aggregations during background analysis
- Index by sector, market_cap, volume for fast filtering
- Maintain materialized views for common queries
- Partition time-series data by date for historical speed

Cache Strategy:
- Sector sentiment scores: 30-minute Redis cache
- Stock universe list: 24-hour cache with daily refresh
- Top 3 picks per sector: Real-time cache with change detection
- Historical patterns: 7-day cache for backtesting

Memory Management:
- Load full universe into memory at startup
- Incremental updates for price changes only
- Garbage collection optimization for continuous operation
- Connection pooling for database efficiency
```

**Error Handling and Reliability:**
```
Graceful Degradation Strategy:

API Failure Scenarios:
1. Polygon.io timeout → Fall back to FMP data
2. FMP unavailable → Use cached sector ETF proxies  
3. Both sources down → Display last known good data with staleness warning
4. Partial data available → Show available sectors, flag missing ones

Performance Degradation:
1. High load detected → Increase cache TTL to reduce calculations
2. Database slow → Serve Redis cache exclusively
3. Memory pressure → Reduce universe size temporarily
4. Network issues → Queue updates for batch processing

User Experience Maintenance:
- Always show something (never blank screen)
- Clear indicators of data freshness and reliability
- Graceful error messages with expected resolution time
- Fallback to basic functionality if advanced features fail
```

**Deliverables:**
- Sub-1-second sector grid loading with Redis optimization
- 3-5 minute on-demand analysis with progress tracking
- <500ms WebSocket latency for real-time updates
- Comprehensive error handling and graceful degradation system

---

### Week 4: User Interface & Integration

#### Day 22-24: Sector Dashboard UI

**Strategic Logic: Trader-Focused Interface Design**

**Desktop-First Design Philosophy:**
Small-cap intraday traders typically use multi-monitor setups and need information density over visual aesthetics. The interface prioritizes actionable intelligence and rapid decision-making.

**4 Sectors Per Row Layout Strategy:**
```
SCREEN_LAYOUT_STRATEGY = {
    'desktop_1920px_plus': {
        'sectors_per_row': 4,
        'card_width': '400px',
        'total_width': '1700px_with_margins',
        'information_density': 'high',
        'target_users': 'primary_intraday_traders'
    },
    'tablet_768_1200px': {
        'sectors_per_row': 2,
        'card_width': '350px', 
        'total_width': '750px_with_margins',
        'information_density': 'medium',
        'target_users': 'mobile_monitoring'
    }
}
```

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

**Multi-Timeframe Visual Strategy:**
```
Timeframe Indicator Design:
- 30M: Most recent momentum (4 AM - 8 PM updates)
- 1D: Current session performance (includes after-hours)
- 3D: Short-term trend confirmation
- 1W: Sector cycle context

Color Consistency Rules:
- All timeframes show same color = high confidence signal
- Mixed colors = transitional period, increased caution
- Recent vs longer-term divergence = potential reversal signal

Example Interpretation:
30M: 🔴  1D: 🔴  3D: 🔴  1W: 🔵 = Strong short-term bearish in longer-term neutral
30M: 🟢  1D: 🟢  3D: 🟢  1W: 🟢 = Consistent bullish across all timeframes
30M: 🔵  1D: 🔴  3D: 🟢  1W: 🟢 = Mixed signals, wait for clarity
```

**Deliverables:**
- Responsive 12-slot grid (4x3 layout for desktop, flexible for tablet)
- Color-coded sector cards for 11 FMP sectors + distinctive theme slot
- Multi-timeframe indicators (30min/1D/3D/1W) per sector card
- Top 3 bullish/bearish stock display with volume confirmation
- Theme slot placeholder with different visual styling

#### Day 25-26: Real-Time Updates

**Strategic Logic: Live Data Integration Framework**

**WebSocket Update Strategy:**
```
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

**Real-Time Update Examples:**
```
Example Update Sequence:

11:47 AM Update:
- OCUL suddenly jumps +25% on FDA announcement
- Healthcare sector recalculated from +0.58 to +0.78
- Sector card transitions from Light Green to Dark Green
- OCUL moves from #2 to #1 in Healthcare bullish list
- WebSocket pushes update to all connected users
- Visual transition: fade to new color, highlight OCUL move

2:15 PM Update:  
- Technology sector 30-minute calculation completes
- SOUN drops from -8.2% to -12.1% (additional decline)
- BBAI volume spikes to 4.2x average on sympathy selling
- Tech sector moves from -0.73 to -0.81 (deeper bearish)
- Color remains Dark Red but intensity indicator updates
- Top bearish reranking: SOUN moves to #1, BBAI to #2
```

**Network Reliability and Performance:**
```
Connection Management:
- Automatic reconnection on connection loss
- Exponential backoff for repeated connection failures
- Heartbeat monitoring to detect stale connections
- Queue updates during brief disconnections

Performance Optimization:
- Compress WebSocket messages for mobile users
- Batch multiple small updates into single message
- Debounce rapid consecutive updates (max 1 per second)
- Client-side caching to reduce redundant data transfer

Error Handling:
- Clear indication of real-time vs cached data
- Manual refresh button always available
- Graceful degradation to polling if WebSocket unavailable
- User notification of any data staleness issues
```

**Deliverables:**
- WebSocket real-time update system with <100ms latency
- Visual change detection with smooth transition animations
- Automatic reconnection and error handling
- Manual refresh capability and connection status monitoring

#### Day 27-28: Testing & Deployment

**Strategic Logic: Production Readiness Validation**

**Comprehensive Testing Strategy:**
```
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

**Production Deployment Validation:**
```
Deployment Checklist:

Environment Setup:
✓ PostgreSQL + TimescaleDB configured with proper indexes
✓ Redis cache configured with appropriate memory allocation  
✓ API keys securely stored and properly accessed
✓ WebSocket server configured for persistent connections
✓ Background job scheduler configured for 8 PM/4 AM/8 AM analysis

Data Pipeline Testing:
✓ Polygon.io MCP connection verified with small-cap universe
✓ FMP MCP connection tested for sector validation
✓ Stock universe filtering produces ~1,500 stocks
✓ Sector classification correctly assigns all small-caps
✓ Multi-timeframe calculations produce expected results

Performance Validation:
✓ Sector grid loads in <1 second consistently
✓ On-demand analysis completes within 5 minutes
✓ WebSocket updates deliver in <100ms
✓ Database queries average <500ms response time
✓ Memory usage remains stable over 24-hour operation

User Experience Testing:
✓ All sector cards display correctly across screen sizes
✓ Color transitions work smoothly for sentiment changes
✓ Top 3 stock lists update appropriately
✓ Real-time updates display without user action required
✓ Error conditions handle gracefully with clear messaging
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
```
Local Server Deployment Setup:

Docker Compose Configuration:
- PostgreSQL with TimescaleDB extension
- Redis with persistence configuration
- FastAPI backend with environment variables
- Next.js frontend with WebSocket client
- Nginx reverse proxy for SSL termination

Security Configuration:
- SSL/TLS certificates for secure connections
- API key encryption and secure storage
- Database connection pooling and access controls
- CORS configuration for WebSocket connections
- Rate limiting for API endpoints

Monitoring Setup:
- Health check endpoints for all services
- Performance monitoring for database queries
- Memory and CPU usage tracking
- Error logging with appropriate detail levels
- WebSocket connection monitoring and alerting
```

**Deliverables:**
- Comprehensive test suite with 90%+ coverage
- Load testing validation for 5+ concurrent users
- Production deployment configuration with security hardening
- Performance monitoring and health check system

---

## 🧠 SLICE 1B: Intelligence Framework (Strategic Logic & Implementation)

### Overview
Transform the basic sector dashboard into a sophisticated manipulation detection and theme intelligence system that helps traders avoid pump-and-dump schemes and momentum traps.

### Strategic Objectives
- **Theme Detection:** Identify cross-sector narratives before they become obvious
- **Contagion Mapping:** Predict sympathy plays across sector boundaries  
- **Temperature Tracking:** Real-time momentum monitoring with "too hot" warnings
- **Manipulation Detection:** Early-stage pump identification and squeeze avoidance

---

### Week 5-6: Theme Detection Engine

#### Strategic Logic: Cross-Sector Narrative Intelligence

**Theme Detection Methodology:**
The system monitors SEC filings, press releases, and news flow to identify emerging market narratives that transcend traditional sector boundaries.

**Keyword-Based Theme Classification:**
```
THEME_DETECTION_FRAMEWORK = {
    'bitcoin_treasury': {
        'primary_keywords': ['bitcoin treasury', 'btc holdings', 'digital asset strategy'],
        'secondary_signals': ['cryptocurrency reserve', 'bitcoin allocation', 'digital gold'],
        'small_cap_examples': ['BTCS', 'GREE', 'HIVE', 'RIOT'],
        'cross_sector_impact': 'affects_tech_energy_finance_sectors',
        'manipulation_risk': 'EXTREME - retail momentum driven'
    },
    'ai_transformation': {
        'primary_keywords': ['artificial intelligence', 'ai integration', 'machine learning'],
        'secondary_signals': ['generative ai', 'ai-powered', 'neural networks'],
        'small_cap_examples': ['SOUN', 'BBAI', 'PATH', 'SMCI'],
        'cross_sector_impact': 'affects_tech_healthcare_industrial_sectors',
        'manipulation_risk': 'HIGH - narrative driven valuation'
    },
    'biotech_catalyst': {
        'primary_keywords': ['fda approval', 'phase iii', 'breakthrough therapy'],
        'secondary_signals': ['orphan designation', 'clinical trial', 'drug candidate'],
        'small_cap_examples': ['OCUL', 'KPTI', 'DTIL', 'VRTX'],
        'cross_sector_impact': 'primarily_healthcare_some_tech_overlap',
        'manipulation_risk': 'MODERATE - event driven volatility'
    },
    'quantum_computing': {
        'primary_keywords': ['quantum computing', 'quantum processor', 'qubit technology'],
        'secondary_signals': ['quantum advantage', 'quantum supremacy', 'quantum algorithms'],
        'small_cap_examples': ['RGTI', 'QMCO', 'IBM', 'GOOGL'],
        'cross_sector_impact': 'affects_tech_defense_financial_sectors',
        'manipulation_risk': 'HIGH - speculative technology'
    }
}
```

**SEC Filing Analysis Strategy:**
```
Filing Monitoring System:

8-K Filing Analysis:
- Keyword density scanning for theme emergence
- Filing frequency analysis (multiple companies, same theme)
- Timing correlation with stock price movements
- Cross-company narrative consistency validation

Example Theme Detection:
Date: January 15, 2025
- BTCS files 8-K: "Board approves Bitcoin treasury strategy"
- GREE files 8-K: "Exploring digital asset allocation" 
- HIVE files 8-K: "Bitcoin reserve consideration"
→ System flags "Bitcoin Treasury" theme emergence
→ All crypto-adjacent small caps marked for monitoring
→ Temperature tracking initiated across theme network

10-Q Analysis:
- Business model pivot identification
- Revenue stream transformation mentions
- Strategic initiative announcements
- Forward-looking statement theme clustering
```

**News Sentiment Integration:**
```
Real-Time News Flow Analysis:

Theme Momentum Tracking:
- News article frequency by theme keywords
- Sentiment analysis of theme coverage (positive/negative/neutral)
- Social media mention velocity and sentiment
- Financial media coverage intensity

Small-Cap Theme Detection Example:
Week 1: 5 articles mention "AI transformation"
Week 2: 12 articles mention AI pivot by small caps
Week 3: 28 articles + 3 TV mentions + analyst coverage
→ Theme classified as "EMERGING → HOT"
→ All AI-related small caps flagged for momentum risk
→ Temperature tracking escalated to hourly monitoring

News Source Prioritization:
- SEC filings: Highest weight (official company statements)
- Financial news wires: High weight (Bloomberg, Reuters, MarketWatch)
- Trade publications: Medium weight (industry-specific insights)
- Social media: Low weight (sentiment confirmation only)
```

**Cross-Sector Contamination Detection:**
```
Theme Spread Analysis:

Bitcoin Treasury Example:
Primary Sector: Technology (SOUN, BBAI shifting strategy)
Secondary Contamination: Energy (GREE, HIVE mining operations)
Tertiary Spread: Finance (SOFI, LC considering crypto services)
→ System maps contamination spread
→ Flags stocks in "infected" sectors for theme monitoring
→ Adjusts sector sentiment scores for theme influence

AI Transformation Example:
Primary Sector: Technology (BBAI, SOUN core business)
Secondary Contamination: Healthcare (DTIL using AI for gene editing)
Tertiary Spread: Industrial (FSR using AI for manufacturing)
→ Cross-sector theme network identified
→ Sympathy play prediction activated
→ Temperature monitoring across all contaminated sectors
```

**Implementation Framework:**
- **Filing Parser:** Real-time SEC EDGAR monitoring with keyword extraction
- **News Aggregator:** Multi-source news feed with theme classification
- **Cross-Reference Engine:** Theme consistency validation across multiple sources
- **Contamination Mapper:** Cross-sector theme spread identification and tracking

---

### Week 7-8: Sympathy Network Analysis

#### Strategic Logic: Correlation-Based Prediction Framework

**Sympathy Network Mapping Strategy:**
The system identifies which small-cap stocks historically move together during specific themes and market conditions.

**Rolling Correlation Analysis:**
```
SYMPATHY_NETWORK_DETECTION = {
    'correlation_window': '14_days_rolling',
    'minimum_correlation': '0.65_threshold',
    'volume_confirmation': 'both_stocks_above_1.5x_average',
    'theme_context': 'active_narrative_required',
    'small_cap_universe': '1500_stock_focus'
}

Example Network Detection:
Bitcoin Treasury Theme Analysis (14-day rolling):
- BTCS vs GREE correlation: 0.78 (strong)
- BTCS vs HIVE correlation: 0.71 (strong)  
- GREE vs HIVE correlation: 0.83 (very strong)
→ Bitcoin Treasury Network identified: [BTCS, GREE, HIVE]
→ When any member moves >10%, flag entire network
→ Temperature escalation for all network members
```

**Primary Mover Identification:**
```
Network Leadership Analysis:

Bitcoin Treasury Network:
Primary Mover: BTCS (usually moves first, others follow)
Secondary Movers: GREE, HIVE (follow within 1-2 hours)
Correlation Strength: BTCS leads 73% of network moves >15%

AI Theme Network:
Primary Mover: SMCI (market cap leader, institutional following)
Secondary Movers: SOUN, BBAI (follow within same session)
Correlation Strength: SMCI leads 68% of AI network moves >10%

Biotech Catalyst Network:
Primary Mover: Variable (depends on specific catalyst/company)
Secondary Movers: Other biotechs with similar indications
Correlation Strength: Catalyst-specific, not consistent leadership
```

**Real-Time Sympathy Prediction:**
```
Sympathy Alert Generation:

Trigger Event Example:
11:23 AM: BTCS sudden volume spike (5.2x average)
11:27 AM: BTCS up +18% on "Bitcoin treasury expansion" news
11:28 AM: System triggers sympathy network alert

Immediate Actions:
→ Flag GREE, HIVE for "SYMPATHY EXPECTED" within 30 minutes
→ Escalate temperature to "HOT" for entire Bitcoin Treasury theme
→ Issue trader alert: "Avoid shorts on Bitcoin Treasury network"
→ Monitor for confirmation: GREE volume spike +25 minutes

Validation at 11:55 AM:
→ GREE +12% (sympathy confirmed)
→ HIVE +8% (sympathy confirmed)
→ Network prediction accuracy logged for algorithm improvement
→ Temperature maintained at "HOT" until momentum subsides
```

**Cross-Sector Sympathy Detection:**
```
Advanced Correlation Analysis:

AI Theme Cross-Sector Example:
Technology Sector: SOUN +15% on AI partnership announcement
→ Expected sympathy: BBAI, PATH (same sector, direct correlation)
→ Cross-sector prediction: DTIL (healthcare AI), FSR (industrial AI)
→ Monitoring period: 2 hours for cross-sector confirmation
→ Volume requirement: 2x average to confirm legitimate sympathy

Biotech FDA Catalyst Example:
OCUL +45% on FDA breakthrough designation (ophthalmology)
→ Direct sympathy: Other ophthalmology biotechs
→ Broader sympathy: Small biotech with similar stage programs
→ Cross-sector: Healthcare tech companies with FDA exposure
→ Validation: Track which predictions materialize vs. false signals
```

**Network Reliability Scoring:**
```
Sympathy Prediction Confidence:

High Confidence Networks (80%+ prediction accuracy):
- Bitcoin Treasury: BTCS, GREE, HIVE (crypto mining/treasury)
- AI Hardware: SMCI, related semiconductor small caps
- Biotech Ophthalmology: OCUL, related eye drug developers

Medium Confidence Networks (60-80% accuracy):
- General AI theme: SOUN, BBAI, PATH (varies by news type)
- Energy transition: Various small cap renewable/battery stocks
- Fintech: SOFI, UPST, AFRM (depends on regulatory environment)

Low Confidence Networks (40-60% accuracy):
- General technology rotation
- Broad sector momentum without specific catalyst
- Market-wide risk-on/risk-off movements

Confidence Adjustment Factors:
+ Theme specificity (Bitcoin Treasury vs. general tech)
+ News catalyst strength (FDA approval vs. earnings beat)
+ Volume confirmation on primary mover
+ Time of day (morning moves more predictive than late day)
```

**Implementation Framework:**
- **Correlation Engine:** Rolling 14-day correlation matrix for 1,500 stock universe
- **Network Mapper:** Dynamic relationship identification based on theme context
- **Prediction Algorithm:** Real-time sympathy probability scoring
- **Validation System:** Track prediction accuracy for continuous improvement

---

### Week 9-10: Hourly Temperature System

#### Strategic Logic: Momentum Temperature Classification

**Temperature Monitoring Framework:**
Track theme and individual stock momentum intensity on hourly basis during full extended trading session (4 AM - 8 PM ET).

**Temperature Classification System:**
```
MOMENTUM_TEMPERATURE_SCALE = {
    'cold': {
        'range': '0-5%_move_normal_volume',
        'signal': 'NORMAL_ANALYSIS_APPLIES',
        'trading_action': 'standard_sector_analysis',
        'example': 'SOUN +2% on normal volume'
    },
    'warm': {
        'range': '5-15%_move_elevated_volume',
        'signal': 'INCREASED_CAUTION',
        'trading_action': 'reduced_position_sizing',
        'example': 'BBAI +12% on 2.1x volume (earnings beat)'
    },
    'hot': {
        'range': '15-25%_move_high_volume',
        'signal': 'HIGH_RISK_AVOID_SHORTS',
        'trading_action': 'no_new_short_positions',
        'example': 'OCUL +22% on FDA breakthrough (4.3x volume)'
    },
    'extreme': {
        'range': '25%_plus_move_massive_volume',
        'signal': 'EXTREME_RISK_EXIT_SHORTS',
        'trading_action': 'close_existing_shorts_immediately',
        'example': 'BTCS +45% Bitcoin treasury announcement (8.7x volume)'
    }
}
```

**Hourly Momentum Tracking:**
```
Extended Session Monitoring (4 AM - 8 PM ET):

Hour-by-Hour Temperature Evolution:
4:00 AM - Pre-market open: BTCS +3% on overnight news
5:00 AM - Early pre-market: BTCS +8% as news spreads
6:00 AM - Pre-market active: BTCS +15% with volume surge
7:00 AM - Final pre-market: BTCS +22% approaching "HOT"
8:00 AM - Economic data: BTCS +18% (slight pullback)
9:30 AM - Market open: BTCS +25% (crosses to "EXTREME")

Temperature Escalation Triggers:
→ Cold to Warm: 5% move + 1.5x volume
→ Warm to Hot: 15% move + 2.5x volume + news catalyst
→ Hot to Extreme: 25% move + 4x volume + viral news spread
→ Cooling signals: Volume decline + price consolidation
```

**Volume-Price Momentum Integration:**
```
Multi-Factor Temperature Calculation:

BTCS Example (Extreme Temperature):
Price Movement: +45% (weight: 40%)
Volume Surge: 8.7x average (weight: 30%)
News Catalyst: Bitcoin treasury (weight: 20%)
Technical Breakout: All-time high breach (weight: 10%)
= Temperature Score: 95/100 (EXTREME)

SOUN Example (Warm Temperature):
Price Movement: +12% (weight: 40%)
Volume Surge: 2.1x average (weight: 30%)
News Catalyst: Partnership announcement (weight: 20%)
Technical Setup: Resistance level test (weight: 10%)
= Temperature Score: 62/100 (WARM)

Cooling Detection Example:
OCUL Hour 1: +45% on 5.2x volume (EXTREME)
OCUL Hour 2: +38% on 3.1x volume (still EXTREME)
OCUL Hour 3: +35% on 1.8x volume (cooling to HOT)
OCUL Hour 4: +32% on 1.2x volume (cooling confirmed)
→ Temperature downgrade triggers: "Potential short entry zone"
```

**Theme-Level Temperature Aggregation:**
```
Bitcoin Treasury Theme Temperature:
Individual Stock Temperatures:
- BTCS: EXTREME (+45%)
- GREE: HOT (+22%)  
- HIVE: WARM (+12%)
- RIOT: HOT (+19%)

Theme Temperature Calculation:
Average: (EXTREME + HOT + WARM + HOT) / 4 = HOT
Weighted by market cap: Emphasize larger positions
Network effect bonus: Multiple stocks hot = theme escalation
→ Final Theme Temperature: EXTREME
→ Trading Signal: "AVOID ALL Bitcoin Treasury related shorts"
```

**Cooling Detection and Re-Entry Signals:**
```
Temperature Decline Identification:

Cooling Pattern Recognition:
Hour 1: EXTREME (25%+ move, 4x+ volume)
Hour 2: EXTREME (sustained, 3x+ volume)
Hour 3: HOT (price consolidation, 2x volume)
Hour 4: WARM (volume normalization, <2x)
Hour 5: COLD (normal trading range resumed)

Re-Entry Signal Generation:
→ 3 consecutive hours of temperature decline
→ Volume return to <1.5x average
→ No new catalyst announcements
→ Technical indicators showing exhaustion
→ Issue trader alert: "Theme cooling - monitor for short opportunities"

False Cooling Detection:
→ Brief temperature decline followed by re-acceleration
→ New catalyst emerges during cooling phase
→ Sympathy network member suddenly heats up
→ System maintains elevated caution until confirmed cooling
```

**Implementation Framework:**
- **Real-Time Monitor:** Continuous price/volume tracking during 4 AM - 8 PM
- **Temperature Calculator:** Multi-factor scoring algorithm with hourly updates
- **Cooling Detector:** Pattern recognition for momentum exhaustion
- **Alert System:** Real-time temperature change notifications to traders

---

### Week 11-12: Manipulation Detection Patterns

#### Strategic Logic: Pump & Dump Pattern Recognition

**Manipulation Cycle Detection:**
Identify the typical phases of small-cap manipulation schemes to provide early warnings and exit signals.

**Manipulation Phase Classification:**
```
MANIPULATION_CYCLE_PHASES = {
    'accumulation': {
        'characteristics': 'unusual_volume_no_news_insider_buying',
        'duration': '2-4_weeks_typical',
        'signals': 'volume_above_average_price_consolidation_form_4_filings',
        'trader_action': 'FLAG_FOR_MONITORING',
        'small_cap_example': 'EXPR: 3 weeks of 1.5x volume, no news, insider Form 4s'
    },
    'markup_initiation': {
        'characteristics': 'price_breakout_volume_surge_narrative_building',
        'duration': '3-7_days_typical',
        'signals': 'breakout_from_range_news_releases_social_media_buzz',
        'trader_action': 'AVOID_SHORTS_MOMENTUM_BUILDING',
        'small_cap_example': 'SOUN: Breaks $4 resistance, AI partnership PR, Twitter buzz'
    },
    'markup_acceleration': {
        'characteristics': 'parabolic_moves_massive_volume_retail_fomo',
        'duration': '1-3_days_peak_intensity',
        'signals': 'daily_gains_15_plus_volume_3x_plus_mainstream_coverage',
        'trader_action': 'EXTREME_CAUTION_NO_SHORTS',
        'small_cap_example': 'BTCS: +45% day, 8x volume, CNBC mentions'
    },
    'distribution': {
        'characteristics': 'high_volume_selling_insider_sales_narrative_peak',
        'duration': '1-2_weeks_selling_pressure',
        'signals': 'volume_stays_high_price_volatile_form_4_selling',
        'trader_action': 'POTENTIAL_SHORT_ENTRY_ZONE',
        'small_cap_example': 'GME: High volume, price volatility, insider sales'
    },
    'decline': {
        'characteristics': 'momentum_exhaustion_retail_exit_volume_decline',
        'duration': '2-8_weeks_return_to_normal',
        'signals': 'volume_normalization_price_decline_interest_fade',
        'trader_action': 'SAFE_SHORT_ENTRY_CONFIRMED',
        'small_cap_example': 'AMC: Volume drops to normal, price declines steadily'
    }
}
```

**Accumulation Phase Detection:**
```
Early Warning System:

Volume Anomaly Detection:
Normal KOSS trading: 400K daily average volume
Week 1: 650K average (1.6x - mild elevation)
Week 2: 720K average (1.8x - continued elevation)  
Week 3: 810K average (2.0x - significant elevation)
→ System flags KOSS for "unusual accumulation pattern"

Insider Activity Correlation:
Form 4 Analysis:
- Week 1: CEO purchases 50K shares
- Week 2: CTO purchases 25K shares
- Week 3: Board member purchases 15K shares
→ Pattern: Coordinated insider buying during volume elevation
→ Alert: "Potential accumulation phase - monitor for breakout"

News Flow Analysis:
- Minimal news during accumulation (avoid detection)
- Occasional positive but non-material updates
- Lack of negative catalysts (clearing the runway)
→ Combined Signal: Volume + Insider + News absence = Accumulation
```

**Markup Phase Recognition:**
```
Breakout and Narrative Building:

Technical Breakout Confirmation:
EXPR accumulation example:
- 6 weeks consolidation between $2.80-$3.20
- Volume averaging 1.8x during consolidation
- Day 43: Breaks above $3.20 on 3.2x volume
- Day 44: Continues to $3.65 (+14% from breakout)
→ System classification: "MARKUP INITIATION" phase

Narrative Development Tracking:
PR Release Timeline:
Day 1: "EXPR announces strategic review of operations"
Day 3: "EXPR exploring AI integration opportunities"  
Day 7: "EXPR partners with undisclosed AI company"
Day 12: "EXPR AI transformation ahead of schedule"
→ Pattern: Escalating narrative building during markup
→ Alert: "Narrative-driven momentum - avoid shorts"

Social Media Amplification:
- Twitter mentions increase from 12/day to 180/day
- Reddit discussions emerge in wallstreetbets
- YouTube videos from "analysts" appear
→ Retail FOMO building indicator
```

**Distribution Phase Identification:**
```
Peak Identification and Selling Detection:

Volume/Price Divergence:
BTCS distribution example:
Day 1: +45% on 8.7x volume (parabolic peak)
Day 2: +12% on 6.2x volume (momentum slowing)
Day 3: -3% on 4.8x volume (first red day, still high volume)
Day 4: +8% on 3.1x volume (dead cat bounce)
Day 5: -8% on 2.9x volume (distribution confirmed)
→ Pattern: High volume continues but price becomes volatile
→ Signal: "Distribution phase detected - monitor for short entry"

Insider Selling Detection:
Form 4 Filing Analysis:
Week 1 of peak: CEO sells 200K shares
Week 2 of peak: CTO sells 100K shares
Week 3 of peak: CFO sells 150K shares
→ Pattern: Coordinated insider selling during price peak
→ Alert: "Insider distribution detected - short setup developing"

Mainstream Media Peak:
- CNBC segment on stock's amazing run
- MarketWatch feature article
- Seeking Alpha coverage surge
→ Signal: Maximum exposure reached, retail topped out
```

**False Signal Filtering:**
```
Legitimate vs Manipulation Differentiation:

Legitimate Breakout Characteristics:
- Fundamental catalyst supporting move (FDA approval, earnings beat)
- Sustained business model improvement
- Industry-wide positive trends
- Institutional investor participation
- Reasonable valuation expansion

Manipulation Red Flags:
- No fundamental justification for move
- Vague or promotional press releases
- Sudden narrative pivots (restaurant becomes AI company)
- Retail-heavy volume with limited institutional flow
- Extreme valuation expansion without business growth

OCUL Example (Legitimate):
+45% move on FDA breakthrough therapy designation
- Clear regulatory catalyst
- Validates years of clinical development
- Industry analysts upgrade price targets
- Institutional coverage initiation
→ Classification: "LEGITIMATE CATALYST" not manipulation

EXPR Example (Potential Manipulation):
+35% move on "AI integration exploration"
- Vague announcement with no specifics
- Company has no AI expertise or resources
- Sudden pivot from retail business model
- No institutional analyst coverage or validation
→ Classification: "NARRATIVE MANIPULATION" risk
```

**Implementation Framework:**
- **Pattern Recognition Engine:** Multi-phase cycle detection algorithms
- **Insider Activity Monitor:** Real-time Form 4 filing analysis and correlation
- **Narrative Tracker:** Press release and social media sentiment evolution
- **Volume-Price Analyzer:** Divergence detection and distribution identification

---

### Week 13-14: Cross-Sector Risk Integration

#### Strategic Logic: Unified Decision Framework

**Theme Override System:**
Integrate traditional sector analysis with theme intelligence to provide unified trading recommendations.

**Decision Matrix Integration:**
```
UNIFIED_DECISION_FRAMEWORK = {
    'traditional_sector_analysis': {
        'weight': '60%_base_case',
        'inputs': 'sector_performance_vs_russell_2000',
        'output': 'bullish_bearish_neutral_classification'
    },
    'theme_intelligence_overlay': {
        'weight': '40%_override_potential',
        'inputs': 'active_themes_temperature_sympathy_networks',
        'output': 'avoid_caution_proceed_signals'
    },
    'final_recommendation': {
        'logic': 'theme_can_override_sector_never_vice_versa',
        'safety_principle': 'when_in_doubt_avoid_risk'
    }
}
```

**Real-World Decision Examples:**
```
Example 1: Technology Sector Bearish + Bitcoin Treasury Theme Hot

Traditional Analysis:
- Technology sector: -2.4% (Dark Red, Prime Shorting)
- Small-cap tech showing weakness: SOUN -8%, BBAI -6%
- Standard recommendation: "Short technology small caps"

Theme Intelligence Override:
- Bitcoin Treasury theme: EXTREME temperature
- Cross-sector contamination: Tech companies exploring crypto
- Network analysis: SOUN mentioned crypto interest last quarter
- Override decision: "AVOID shorts in crypto-adjacent tech names"

Final Recommendation:
- Short traditional tech: PATH, SMCI (pure software/hardware)
- AVOID shorting: SOUN, BBAI (potential crypto contamination)
- Sector card display: "TECH 🔴 BEARISH ⚠️ Bitcoin Treasury Active"

Example 2: Healthcare Sector Bullish + FDA Theme Cooling

Traditional Analysis:
- Healthcare sector: +1.8% (Light Green, Avoid Shorts)
- FDA approvals driving biotech rally: OCUL +45%, KPTI +18%
- Standard recommendation: "Avoid all healthcare shorts"

Theme Intelligence Refinement:
- FDA catalyst theme: Temperature cooling from EXTREME to WARM
- Individual stock analysis: OCUL exhaustion signals appearing
- Volume declining: From 5.2x to 1.8x average over 3 hours
- Refinement: "Theme cooling, monitor for reversal opportunities"

Final Recommendation:
- Maintain avoid-shorts for sector leaders: OCUL, KPTI still hot
- Monitor laggards for short opportunities: DTIL if fails to follow
- Sector card: "HEALTHCARE 🟢 BULLISH (Theme Cooling - Monitor)"
```

**Risk Multiplier Application:**
```
Theme Risk Multiplier System:

Base Risk Assessment (Traditional):
SOUN Technology stock in bearish sector:
- Sector bearish: -2.4% (Good shorting environment)
- Stock specific: -8.2% gap, 2.1x volume
- Technical setup: Below resistance, good short setup
- Base recommendation: "SHORTABLE - Good setup"

Theme Risk Multiplier:
AI Theme Active: Temperature = HOT
- Risk multiplier: 2.5x (AI theme actively discussed)
- Cross-sector impact: AI mentions across multiple sectors
- Narrative building: "AI transformation" press releases
- Social media: Increasing AI-related discussion

Final Risk Assessment:
Base Risk × Theme Multiplier = Adjusted Risk
Low Risk × 2.5 = Medium-High Risk
→ Recommendation change: "CAUTION - AI theme active, reduced conviction"

Bitcoin Treasury Example:
BTCS Base assessment: Bearish sector, good short technical setup
Theme multiplier: 5.0x (EXTREME Bitcoin Treasury theme)
→ Final: "DO NOT SHORT - Theme extremely hot, high squeeze risk"
```

**Visual Warning Integration:**
```
Enhanced Sector Card Display:

Financial Sector with Theme Warnings:
┌──────────────────────────────────────────┐
│ FINANCIAL 🔴 BEARISH -1.9%               │
│ ⚠️  BITCOIN TREASURY THEME 🌡️🔥🔥🔥        │
│ 30M: 🔴 -0.5  1D: 🔴 -1.8               │
│ 3D:  🔴 -3.2  1W: 🔴 -4.1               │
├──────────────────────────────────────────┤
│ 📉 SHORTABLE (Traditional Finance):      │
│ • Regional banks, insurance               │
│ • Credit card companies                   │
├──────────────────────────────────────────┤
│ 🚫 AVOID SHORTS (Bitcoin Theme):         │
│ • BTCS, GREE, HIVE (Bitcoin Treasury)    │
│ • SOFI, UPST (Crypto exposure)           │
│ • Any fintech with crypto mentions       │
└──────────────────────────────────────────┘

Technology Sector with AI Theme:
┌──────────────────────────────────────────┐
│ TECHNOLOGY 🔴 BEARISH -2.4%              │
│ ⚠️  AI TRANSFORMATION 🌡️🔥🔥              │
│ 30M: 🔴 -0.8  1D: 🔴 -2.4               │
│ 3D:  🔴 -5.1  1W: 🔵 +1.2               │
├──────────────────────────────────────────┤
│ 📉 SHORTABLE (Traditional Tech):         │
│ • SMCI, PATH (Hardware/Software)         │
│ • Legacy tech without AI pivot           │
├──────────────────────────────────────────┤
│ 🚫 AVOID SHORTS (AI Theme):              │
│ • SOUN, BBAI (AI transformation)         │
│ • Any company mentioning AI pivot        │
└──────────────────────────────────────────┘
```

**Real-Time Theme Status Integration:**
```
Dynamic Theme Monitoring:

Theme Status Updates:
Bitcoin Treasury Theme Status Change:
9:30 AM: EXTREME (BTCS +45% on treasury news)
11:15 AM: EXTREME (GREE +22% sympathy confirmed)
1:45 PM: HOT (Volume cooling, consolidation)
3:20 PM: WARM (No new catalysts, momentum fading)
4:30 PM: COLD (Volume normalized, theme exhausted)

Sector Card Updates:
→ Theme warning badges update in real-time
→ Temperature indicators change throughout session
→ Stock avoidance lists adjust dynamically
→ Trading recommendations update automatically

Trader Alert System:
"Bitcoin Treasury theme cooling - BTCS, GREE may become shortable"
"AI theme heating up - Avoid shorts on SOUN, BBAI network"
"FDA theme exhausted - Healthcare short opportunities emerging"
```

**Implementation Framework:**
- **Decision Engine:** Traditional sector analysis + theme intelligence integration
- **Risk Calculator:** Dynamic risk multiplier application based on theme temperature
- **Visual System:** Enhanced sector cards with theme warnings and specific stock guidance
- **Alert Generator:** Real-time theme status change notifications with trading implications

---

## 📊 Success Metrics & Validation

### Slice 1A Success Criteria
- **Performance:** Sector grid loads in <1 second consistently
- **Accuracy:** 75%+ directional sector prediction (4-hour windows)
- **Reliability:** Background analysis completes within 5 minutes
- **Coverage:** 1,500+ small-cap universe maintained daily
- **User Experience:** On-demand analysis completes in 3-5 minutes

### Slice 1B Success Criteria (Projected)
- **Theme Detection:** Identify emerging themes within 24-48 hours of inception
- **Avoidance Accuracy:** 80%+ success avoiding "too hot" momentum traps and squeeze scenarios
- **Network Mapping:** 90%+ accuracy identifying primary sympathy relationships and follow-through
- **Temperature Tracking:** Real-time status updates during 4 AM - 8 PM extended sessions
- **Risk Reduction:** Measurable reduction in short-squeeze exposure through theme awareness
- **False Signal Rate:** <20% false positive rate on manipulation pattern detection

### Combined System Validation
- **Decision Accuracy:** Theme override decisions prove correct 85%+ of the time
- **Risk Management:** Significant reduction in unexpected losses from theme-driven momentum
- **User Adoption:** Traders actively use theme warnings to modify traditional sector analysis
- **Performance Impact:** No degradation in Slice 1A performance with Slice 1B integration

---

## 📊 Success Metrics & Validation

### Slice 1A Success Criteria
- **Performance:** Sector grid loads in <1 second
- **Accuracy:** 75%+ directional sector prediction (4-hour windows)
- **Reliability:** Background analysis completes within 5 minutes
- **Coverage:** 1,500+ small-cap universe maintained daily
- **Responsiveness:** On-demand analysis completes in 3-5 minutes

### Slice 1B Success Criteria (Projected)
- **Theme Detection:** Identify emerging themes within 24 hours
- **Avoidance Accuracy:** 80%+ success avoiding "too hot" momentum traps
- **Network Mapping:** 90%+ accuracy identifying primary sympathy relationships
- **Temperature Tracking:** Real-time status updates during 4 AM - 8 PM sessions
- **Risk Reduction:** Measurable reduction in short-squeeze exposure

---

## 🚀 Deployment Strategy

### Local Development Phase
- **Environment:** PostgreSQL + TimescaleDB + Redis local stack
- **Data Sources:** Polygon.io MCP ($29/month) + FMP MCP (free tier)
- **Testing:** Single user, development feature validation
- **Timeline:** Week 1-4 (Slice 1A completion)

### Local Server Deployment
- **Environment:** Personal server with production-ready security
- **User Base:** 1-5 beta testers
- **Monitoring:** Basic health checks and performance metrics
- **Timeline:** Week 4+ (post Slice 1A testing)

### Small Group Testing (Future)
- **Environment:** Enhanced local + cloud backup
- **User Base:** 10-20 active traders
- **Features:** Slice 1A + initial Slice 1B components
- **Timeline:** Month 2-3 (post Slice 1B framework implementation)

---

## ⚠️ Risk Considerations & Mitigation

### Technical Risks
- **API Dependencies:** Implement fallback data sources and graceful degradation
- **Performance Scaling:** Design with horizontal scaling capabilities from start
- **Data Quality:** Multi-source validation and error detection systems

### Market Risks  
- **Theme Emergence:** Build adaptive detection vs. pre-programmed themes
- **False Signals:** Implement confidence scoring and validation periods
- **Manipulation Evolution:** Design flexible pattern recognition vs. fixed rules

### User Experience Risks
- **Complexity Overload:** Maintain simple visual interface despite sophisticated backend
- **Analysis Paralysis:** Clear go/no-go signals vs. overwhelming data
- **Timing Misalignment:** Flexible analysis scheduling vs. rigid timing

---

*This implementation plan provides a comprehensive roadmap for building the sector-first small-cap sentiment analysis platform, with Slice 1A delivering immediate trader value and Slice 1B framework positioned for sophisticated manipulation detection capabilities.*