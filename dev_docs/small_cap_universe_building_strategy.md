# Small Cap Universe Building Strategy

## Overview
This document outlines the strategy for building and maintaining a universe of small-cap stocks for sector sentiment analysis.

## Original Strategy (Pre-Testing)
Initial approach based on SDD requirements:

### Market Cap Criteria
- **Minimum**: $10M market cap
- **Maximum**: $2B market cap
- **Target**: Small-cap focus avoiding micro-caps and mid-caps

### Volume & Price Filters
- **Volume**: 1M+ daily volume (original SDD target)
- **Price**: $1.00+ (original SDD target)
- **Upper Price Limit**: $100.00 (to avoid high-priced stocks)

### Exchange Selection
- **Primary**: NASDAQ, NYSE
- **Rationale**: Major exchanges for liquidity and reliability

### FMP API Configuration
```javascript
stockScreener({
  marketCapMoreThan: 10_000_000,      // $10M minimum
  marketCapLowerThan: 2_000_000_000,  // $2B maximum
  exchange: 'NASDAQ,NYSE',
  volumeMoreThan: 1_000_000,          // 1M+ volume
  priceMoreThan: 1.00,
  priceLowerThan: 100.00,
  isActivelyTrading: true,
  limit: 5000                         // Max results
})
```

---

## **REAL-WORLD TESTED BENCHMARKS** ⭐
*Updated: July 21, 2025*

### **Working Configuration (Verified)**
After systematic testing with FMP Ultimate API, the following configuration delivers optimal small-cap universe coverage:

#### **Final Optimized Filters**
- **Market Cap**: $10M - $2B (unchanged)
- **Volume Threshold**: **25,000 shares/day** (lowered from 1M)
- **Price Threshold**: **$0.50** (lowered from $1.00)
- **Exchange**: NASDAQ,NYSE (unchanged)
- **Upper Price Limit**: **REMOVED** (no priceLowerThan filter)
- **API Limit**: 5000 (tested sweet spot)

#### **Volume Threshold Testing Results**
| Volume Threshold | Universe Size | Notes |
|------------------|---------------|-------|
| 1,000,000 (1M)   | 373 stocks    | Original SDD target - too restrictive |
| 500,000 (500K)   | 682 stocks    | Still below target |
| 250,000 (250K)   | 1,066 stocks  | Approaching target |
| 100,000 (100K)   | 1,790 stocks  | Close to target |
| **25,000 (25K)**  | **3,073 stocks** | ✅ **OPTIMAL - Exceeds >2k target** |

#### **Final FMP API Call (Working)**
```javascript
{
  "marketCapMoreThan": 10000000,      // $10M
  "marketCapLowerThan": 2000000000,   // $2B  
  "volumeMoreThan": 25000,            // 25K volume (optimized)
  "priceMoreThan": 0.50,              // $0.50 (optimized)
  "exchange": "NASDAQ,NYSE",
  "limit": 5000,                      // Tested sweet spot
  // NO priceLowerThan = no upper price limit
}
```

### **Key Learnings**
1. **Volume was the primary constraint** - reducing from 1M to 25K dramatically increased universe size
2. **Price threshold optimization** - lowering from $1.00 to $0.50 captured more small-caps
3. **Upper price limit removal** - eliminating $100 cap added more coverage
4. **FMP API parameter casing** - CRITICAL: Use camelCase (marketCapMoreThan) not snake_case
5. **Limit parameter importance** - 5000 is the tested sweet spot for comprehensive coverage

### **Production Recommendation**
**Use 25K volume threshold configuration** - delivers 3,073 stocks, significantly exceeding the >2k target while maintaining quality small-cap criteria.

---

## Target Metrics

### Expected Universe Size
- **Real-World Verified**: **3,073 stocks** (25K volume threshold)
- **Original SDD Target**: ~2,000 stocks (theoretical)
- **Quality Threshold**: >2,000 for robust sector analysis

### Sector Distribution
Target representation across 8 core sectors for balanced analysis.

### Update Frequency
- **Daily refresh** during market hours
- **Inactive stock cleanup** before new data retrieval
- **Market cap validation** to maintain small-cap focus

## Implementation Notes

### Database Storage
- Use `stock_universe` table with `is_active` flag for current universe management
- Store both current and historical universe data for analysis

### API Integration
- **Primary**: FMP Ultimate plan for stock screening
- **Backup**: Polygon.io for price data (if needed)
- **Rate Limiting**: Respect API limits with proper throttling

### Quality Assurance
- **Market cap validation**: Ensure all stocks fall within $10M-$2B range
- **Volume verification**: Confirm daily volume meets minimum threshold
- **Exchange validation**: NASDAQ/NYSE only
- **Price validation**: Minimum $0.50, no upper limit

## Troubleshooting

### Common Issues
1. **Universe too small**: Lower volume threshold (test with 25K)
2. **Large-cap contamination**: Verify camelCase API parameters
3. **API parameter errors**: Use camelCase (marketCapMoreThan) not snake_case
4. **Rate limiting**: Implement proper delays between API calls

### Validation Steps
1. Check universe size after build (target: >2k stocks)
2. Verify market cap distribution (should be $10M-$2B)
3. Confirm exchange distribution (NASDAQ/NYSE only)
4. Validate volume threshold compliance