# Small Cap Universe Building Strategy

## Universe Criteria
- **Market Cap Range**: $10M - $2B  
- **Price Range**: $1 - $100
- **Minimum Volume**: 1M+ shares daily
- **Float Requirements**: >5M (micro cap), >10M (small cap)
- **Exchanges**: NASDAQ, NYSE only
- **Exclusions**: OTC, nano float stocks

## Target Universe Size
- **Total Expected**: ~1,200-1,500 stocks
- **Micro Caps**: ~400-600 stocks ($10M-$300M)
- **Small Caps**: ~800-900 stocks ($300M-$2B)

## FMP API Strategy

### Phase 1: Universe Building (1 API Call)
```javascript
// Single efficient call to build entire universe
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

**Result**: ~1,500 stocks with sector/industry data included
**API Calls**: 1 call total
**Time**: <30 seconds

### Phase 2: Sector Classification (Built-in)
FMP screener returns sector/industry data automatically:
- Healthcare & Biotechnology
- Technology & Software  
- Financial Services
- Industrial & Manufacturing
- Consumer Goods & Services
- Energy & Utilities
- Real Estate
- Materials & Basic Industries

### Phase 3: Real-time Updates (Optional)
For daily universe maintenance:
- **Quote Updates**: Use batch quotes (1 call for multiple stocks)
- **Market Cap Changes**: Re-run screener (1 call)
- **Volume Validation**: Use 5-day averages

## API Call Economics

### FMP Plan Requirements
- **Starter Plan**: 300 calls/minute ($15/month)
- **Peak Usage**: ~60 calls/minute (well under limit)
- **Universe Building**: 1 call (instant)
- **Daily Operations**: 10-20 calls

### Efficiency Comparison
| Approach | API Calls | Time | Complexity |
|----------|-----------|------|------------|
| **FMP Screener** | 1 call | 30 sec | Low |
| **Polygon.io Manual** | 3,000+ calls | 10+ min | High |
| **Russell 2000 + Filter** | 100 calls | 2 min | Medium |

## Implementation Phases

### Week 1: FMP Setup & Testing
1. Subscribe to FMP Starter Plan
2. Test stockScreener with our criteria
3. Validate result quality vs. known small caps
4. Measure API response times

### Week 2: Universe Validation
1. Cross-reference with Russell 2000 holdings
2. Validate sector classifications
3. Test volume and float calculations
4. Identify any missing quality stocks

### Week 3: Production Pipeline
1. Build automated universe builder
2. Set up daily refresh process
3. Create sector performance tracking
4. Implement change detection

### Week 4: Monitoring & Optimization
1. Track universe stability
2. Monitor for new IPOs/delistings
3. Validate sector rotation patterns
4. Optimize refresh frequency

## Success Metrics
- ✅ Universe size: 1,200-1,500 stocks
- ✅ Market cap accuracy: >95%
- ✅ Volume threshold compliance: >90%
- ✅ Sector distribution matches expectations
- ✅ API performance: <1 minute total
- ✅ Daily maintenance: <10 API calls

## Risk Mitigation
- **Backup Data Source**: Polygon.io for validation
- **Index Cross-reference**: Russell 2000 completeness check
- **Manual Review**: Sample validation of edge cases
- **Cost Control**: Monitor API usage patterns

## Next Steps
1. Set up FMP subscription with proper plan
2. Run initial screener test
3. Compare results with our Polygon.io sample
4. Validate sector accuracy
5. Build production pipeline