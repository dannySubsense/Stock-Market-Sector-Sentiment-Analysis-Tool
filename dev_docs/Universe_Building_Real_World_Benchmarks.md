# Universe Building Real-World Benchmarks

**Date**: July 21, 2025  
**API**: FMP Ultimate Plan  
**Testing Method**: Systematic volume threshold optimization  
**Goal**: Achieve >2,000 stock universe for robust sector analysis

## 🎯 **FINAL OPTIMIZED CONFIGURATION**

### **Production Settings (Verified)**
```python
MIN_MARKET_CAP = 10_000_000      # $10M minimum
MAX_MARKET_CAP = 2_000_000_000   # $2B maximum  
MIN_VOLUME = 25_000              # 25K shares daily (OPTIMIZED)
MIN_PRICE = 0.50                 # $0.50 minimum (OPTIMIZED)
ALLOWED_EXCHANGES = ["NASDAQ", "NYSE"]
# NO upper price limit (priceLowerThan removed)
# API limit: 5000 (tested sweet spot)
```

### **FMP API Parameters (camelCase - CRITICAL)**
```json
{
  "marketCapMoreThan": 10000000,
  "marketCapLowerThan": 2000000000,
  "volumeMoreThan": 25000,
  "priceMoreThan": 0.50,
  "exchange": "NASDAQ,NYSE",
  "limit": 5000
}
```

## 📊 **VOLUME THRESHOLD TESTING RESULTS**

| Volume Threshold | Universe Size | Performance | Status |
|------------------|---------------|-------------|---------|
| 1,000,000 (1M)   | 373 stocks    | 18.7% of target | ❌ Too restrictive |
| 500,000 (500K)   | 682 stocks    | 34.1% of target | ❌ Below target |
| 250,000 (250K)   | 1,066 stocks  | 53.3% of target | ⚠️ Approaching |
| 100,000 (100K)   | 1,790 stocks  | 89.5% of target | ✅ Close |
| **25,000 (25K)** | **3,073 stocks** | **153.7% of target** | ✅ **OPTIMAL** |

## 🔍 **KEY INSIGHTS**

### **Critical Finding: Volume Was The Primary Constraint**
- Reducing volume threshold from 1M → 25K increased universe by **724%**
- Volume filtering was more restrictive than price or market cap filters
- 25K threshold maintains quality while maximizing coverage

### **Secondary Optimizations**
1. **Price Threshold**: $1.00 → $0.50 (captured more small-caps)
2. **Upper Price Limit**: Removed $100 cap (added coverage)
3. **API Parameters**: Fixed camelCase vs snake_case bug
4. **Limit Parameter**: 5000 confirmed as sweet spot

### **FMP API Lessons Learned**
1. **Parameter Casing**: MUST use camelCase (`marketCapMoreThan`) not snake_case
2. **Silent Failures**: Wrong parameter names silently ignored (no error)
3. **Limit Importance**: 5000 limit captures comprehensive results
4. **Ultimate Plan**: Required for higher rate limits and data access

## 📈 **PROGRESSIVE IMPROVEMENT TIMELINE**

### **Phase 1: Bug Fix (Critical)**
- **Issue**: Large-cap stocks in universe (NVDA, MSFT, AAPL)
- **Root Cause**: snake_case parameters ignored by FMP API
- **Fix**: Changed to camelCase parameters
- **Result**: Fixed filtering, but universe still small (373 stocks)

### **Phase 2: Volume Optimization**
- **Strategy**: Systematic reduction of volume threshold
- **Testing**: 500K → 250K → 100K → 25K
- **Result**: Progressive improvement to 3,073 stocks

### **Phase 3: Secondary Optimizations**
- **Price**: $1.00 → $0.50 (additional coverage)
- **Upper Limit**: Removed $100 cap
- **Result**: Final optimized configuration

## ⚠️ **CRITICAL CONFIGURATION NOTES**

### **DO NOT CHANGE Without Testing**
- **Volume threshold**: 25K is optimal balance of quality vs. coverage
- **API parameters**: camelCase is MANDATORY for FMP
- **Limit parameter**: 5000 is tested sweet spot
- **Exchange filtering**: NASDAQ,NYSE maintains quality

### **Future Optimization Considerations**
- **Market conditions**: Bear markets may require lower thresholds
- **IPO activity**: May naturally increase universe size
- **Sector rotation**: Monitor for balanced sector representation

## 🔬 **VALIDATION METRICS**

### **Universe Quality Checks**
- ✅ Market cap range: $10M - $2B (verified)
- ✅ Exchange compliance: NASDAQ/NYSE only (verified)  
- ✅ Volume compliance: >25K daily (verified)
- ✅ Price compliance: >$0.50 (verified)
- ✅ Active trading: All stocks actively trading (verified)

### **Coverage Analysis**
- **Total Universe**: 3,073 stocks
- **Target Achievement**: 153.7% of >2k goal
- **Sector Distribution**: Balanced across 8 sectors
- **Quality Score**: High-quality small-cap focus maintained

## 📝 **PRODUCTION RECOMMENDATIONS**

### **Use This Configuration**
```python
# Verified optimal settings (July 21, 2025)
MIN_VOLUME = 25_000              # 25K daily volume
MIN_PRICE = 0.50                 # $0.50 minimum
# NO upper price limit
# Market cap: $10M-$2B (unchanged)
# Exchanges: NASDAQ,NYSE (unchanged)
```

### **Monitoring & Maintenance**
1. **Daily universe size check**: Should be ~3k stocks
2. **Market cap validation**: Ensure no large-cap contamination
3. **Volume compliance**: Verify 25K threshold maintained
4. **API parameter verification**: Confirm camelCase usage

### **Emergency Rollback**
If universe becomes too large (>5k stocks), incrementally raise volume threshold:
- Test 50K volume → expect ~2.5k stocks
- Test 75K volume → expect ~2k stocks
- Test 100K volume → confirmed 1,790 stocks

## 🏆 **SUCCESS METRICS ACHIEVED**

- ✅ **Universe Size**: 3,073 stocks (exceeds >2k target)
- ✅ **Quality Maintained**: All small-cap criteria met
- ✅ **API Efficiency**: Single call universe building
- ✅ **Sector Coverage**: Balanced distribution achieved
- ✅ **Production Ready**: Stable, tested configuration

---

**Status**: ✅ **PRODUCTION READY**  
**Configuration**: **LOCKED & VERIFIED**  
**Next Step**: Implement price data retrieval for this universe 