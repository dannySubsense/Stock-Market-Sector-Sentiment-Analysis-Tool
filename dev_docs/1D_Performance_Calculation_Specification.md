# 1D Performance Calculation Specification

## 🎯 **Objective**: Define exact mathematical formulas for 1D sector sentiment calculation

**Version**: 1.0  
**Scope**: Single timeframe (1D) calculation with IWM benchmark  
**Data Source**: Real-time stock price and volume data  

---

## 📊 **Mathematical Formulas**

### **1. Individual Stock Performance Calculation**

```python
# Basic percentage change formula
stock_performance = (current_price - previous_close) / previous_close * 100

# Input validation:
# - current_price > 0
# - previous_close > 0  
# - Reasonable change threshold: abs(stock_performance) < 50%
```

### **2. Volume Weighting Calculation**

```python
# Volume ratio calculation
volume_ratio = current_volume / avg_20_day_volume

# Volume weight application (with safety caps)
volume_weight = min(max(volume_ratio, 0.1), 10.0)  # Cap between 0.1x and 10.0x

# Weighted stock performance
weighted_performance = stock_performance * volume_weight
```

### **3. Sector Aggregation Formula**

```python
# Sector-level aggregation
sector_stocks = get_stocks_in_sector(sector_name)
total_weighted_performance = 0.0
total_weights = 0.0

for stock in sector_stocks:
    volume_weight = calculate_volume_weight(stock)
    weighted_perf = stock.performance * volume_weight
    
    total_weighted_performance += weighted_perf
    total_weights += volume_weight

# Average weighted performance
sector_raw_performance = total_weighted_performance / total_weights

# Apply sector volatility multiplier
volatility_multiplier = get_volatility_multiplier(sector_name)
sector_final_performance = sector_raw_performance * volatility_multiplier
```

### **4. IWM Benchmark Calculation**

```python
# IWM (Russell 2000) performance calculation
iwm_performance = (iwm_current_price - iwm_previous_close) / iwm_previous_close * 100

# Sector relative performance (alpha)
sector_alpha = sector_final_performance - iwm_performance

# Relative strength classification
if sector_alpha > 2.0:
    relative_strength = "STRONG_OUTPERFORM"
elif sector_alpha > 0.5:
    relative_strength = "OUTPERFORM"
elif sector_alpha > -0.5:
    relative_strength = "NEUTRAL"
elif sector_alpha > -2.0:
    relative_strength = "UNDERPERFORM"
else:
    relative_strength = "STRONG_UNDERPERFORM"
```

---

## 🔢 **Data Requirements**

### **Required Stock Data Fields**
| Field | Type | Source | Validation |
|-------|------|--------|------------|
| `symbol` | string | Universe | 1-5 chars, uppercase |
| `current_price` | float | API | > 0, < 1000 |
| `previous_close` | float | API | > 0, < 1000 |
| `current_volume` | int | API | >= 0 |
| `avg_20_day_volume` | int | API/Calc | > 0 |
| `sector` | string | Universe | Valid sector name |

### **Required Benchmark Data**
| Field | Type | Source | Validation |
|-------|------|--------|------------|
| `iwm_current_price` | float | API | > 0 |
| `iwm_previous_close` | float | API | > 0 |

### **Configuration Data**
| Field | Type | Source | Range |
|-------|------|--------|-------|
| `volatility_multiplier` | float | Config | 0.5 - 2.0 |

---

## ⚙️ **Processing Steps**

### **Step-by-Step Calculation Process**

1. **Data Validation Phase**
   ```python
   # Validate all input data meets requirements
   # Remove stocks with invalid/missing data
   # Log data quality metrics
   ```

2. **Individual Stock Calculation Phase**
   ```python
   for each stock in sector:
       stock.performance = calculate_stock_performance(stock)
       stock.volume_weight = calculate_volume_weight(stock)
       stock.weighted_performance = stock.performance * stock.volume_weight
   ```

3. **Sector Aggregation Phase**
   ```python
   sector.raw_performance = sum(weighted_performances) / sum(weights)
   sector.final_performance = sector.raw_performance * volatility_multiplier
   ```

4. **Benchmark Comparison Phase**
   ```python
   iwm.performance = calculate_iwm_performance()
   sector.alpha = sector.final_performance - iwm.performance
   sector.relative_strength = classify_relative_strength(sector.alpha)
   ```

5. **Output Generation Phase**
   ```python
   return SectorPerformance(
       sector_name=sector,
       performance_1d=sector.final_performance,
       iwm_benchmark=iwm.performance,
       alpha=sector.alpha,
       relative_strength=sector.relative_strength,
       confidence=calculate_confidence(data_quality_metrics)
   )
   ```

---

## 🔍 **Edge Case Handling**

### **Missing Data Scenarios**
| Scenario | Handling Strategy | Fallback |
|----------|------------------|----------|
| Zero current volume | Use 1.0x volume weight | Skip if no avg volume |
| Missing previous close | Use last known close | Skip stock |
| Missing avg volume | Use current volume | Volume weight = 1.0 |
| IWM data unavailable | Set benchmark = 0 | Calculate relative to 0 |
| No stocks in sector | Return null performance | Flag as insufficient data |

### **Extreme Value Scenarios**
| Scenario | Threshold | Action |
|----------|-----------|--------|
| Stock performance > 50% | abs(perf) > 50% | Cap at ±50% |
| Volume ratio > 10x | volume_ratio > 10.0 | Cap at 10.0x |
| Volume ratio < 0.1x | volume_ratio < 0.1 | Floor at 0.1x |
| Sector < 3 stocks | stock_count < 3 | Flag low confidence |

---

## 📤 **Output Format Specification**

### **SectorPerformance1D Data Structure**
```python
@dataclass
class SectorPerformance1D:
    # Core performance data
    sector_name: str
    performance_1d: float  # Final sector performance percentage
    timestamp: datetime
    
    # Benchmark comparison
    iwm_benchmark: float  # IWM 1D performance
    alpha: float  # Sector performance - IWM performance
    relative_strength: str  # STRONG_OUTPERFORM, OUTPERFORM, etc.
    
    # Calculation metadata
    stock_count: int  # Number of stocks included
    confidence: float  # 0.0 to 1.0 based on data quality
    volatility_multiplier: float  # Applied multiplier
    
    # Data quality indicators
    avg_volume_weight: float  # Average volume weight applied
    data_coverage: float  # Percentage of universe with valid data
    calculation_time: float  # Seconds to calculate
```

---

## ✅ **Validation Criteria**

### **Mathematical Accuracy Requirements**
- Percentage calculations accurate to 3 decimal places
- Volume weighting applied consistently across all stocks
- Sector aggregation preserves mathematical integrity
- IWM benchmark calculation matches manual verification

### **Data Quality Requirements**
- Minimum 70% of sector stocks with valid data
- Volume weights within reasonable ranges (0.1x - 10.0x)
- Price changes within reasonable thresholds (±50%)
- Confidence score reflects actual data quality

### **Performance Requirements**
- Single sector calculation: < 100ms
- Full 11-sector calculation: < 5 seconds
- Memory usage: < 50MB for calculation
- No memory leaks during repeated calculations

---

## 🧪 **Test Cases for Validation**

### **Known Input/Output Test Cases**

**Test Case 1: Simple Calculation**
```python
# Input:
stock_data = {
    "SOUN": {"current": 5.00, "previous": 4.50, "volume": 2000000, "avg_volume": 1000000},
    "BBAI": {"current": 3.60, "previous": 4.00, "volume": 1500000, "avg_volume": 1500000}
}
iwm_data = {"current": 200.0, "previous": 198.0}
volatility_multiplier = 1.3

# Expected Output:
# SOUN: +11.11% * 2.0 weight = +22.22% weighted
# BBAI: -10.00% * 1.0 weight = -10.00% weighted
# Sector: (22.22 + -10.00) / (2.0 + 1.0) = +4.07% raw
# Final: +4.07% * 1.3 = +5.29%
# IWM: +1.01%
# Alpha: +5.29% - 1.01% = +4.28%
expected_sector_performance = 5.29
expected_alpha = 4.28
```

**Test Case 2: Edge Case - Zero Volume**
```python
# Input with zero current volume:
stock_data = {
    "TEST": {"current": 10.0, "previous": 9.0, "volume": 0, "avg_volume": 1000000}
}
# Expected: Use 1.0x volume weight, performance = +11.11%
```

**Test Case 3: Extreme Move Capping**
```python
# Input with extreme move:
stock_data = {
    "EXTREME": {"current": 15.0, "previous": 2.0, "volume": 1000000, "avg_volume": 1000000}
}
# Raw performance: +650% -> Capped at +50%
# Expected: performance = +50.00%
```

This specification provides the exact mathematical foundation for implementing 1D sector performance calculation with comprehensive validation and edge case handling. 