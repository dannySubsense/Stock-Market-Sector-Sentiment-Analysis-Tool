# Market Sector Sentiment Analysis Tool
## Slice 1B API Refactoring Plan - Optimize for Future Growth

**Version:** 1.0  
**Target:** Refactor API structure for Slice 1B intelligence features  
**Current State:** 3 routers (health, sectors, stocks)  
**Target State:** 5 routers (health, sectors, stocks, analysis, cache)  
**Timeline:** Post Slice 1A completion, pre Slice 1B implementation

---

## 🎯 Refactoring Objectives

### Primary Goals
- **Separate Analysis Engine:** Isolate analysis functionality for Slice 1B intelligence features
- **Centralize Cache Management:** Create system-wide cache control
- **Prepare for Theme Detection:** Structure for cross-sector intelligence
- **Maintain Backward Compatibility:** Ensure existing endpoints continue working
- **Improve Testability:** Better separation for comprehensive testing

### Success Criteria
- All existing endpoints remain functional
- Analysis engine becomes independent module
- Cache management is system-wide
- Ready for Slice 1B theme detection implementation
- Improved API documentation and testing coverage

---

## 📊 Current vs Target API Structure

### Current Structure (Slice 1A)
```
/api/health/*          # System monitoring (4 endpoints)
/api/sectors/*         # Sector dashboard + analysis (8 endpoints)
/api/stocks/*          # Stock universe management (6 endpoints)
/api/                  # Root endpoint (1 endpoint)
```

### Target Structure (Slice 1B Ready)
```
/api/health/*          # System monitoring (4 endpoints)
/api/sectors/*         # Sector sentiment and display (4 endpoints)
/api/stocks/*          # Stock universe and individual stocks (6 endpoints)
/api/analysis/*        # Analysis engine and scheduling (4 endpoints)
/api/cache/*           # Cache management and performance (3 endpoints)
/api/                  # Root endpoint (1 endpoint)
```

---

## 🔄 Detailed Refactoring Plan

### Phase 1: Analysis Engine Extraction

#### 1.1 Create New Analysis Router
**File:** `backend/api/routes/analysis.py`

**Endpoints to Move:**
- `POST /api/sectors/analysis/on-demand` → `POST /api/analysis/trigger`
- `GET /api/sectors/analysis/status` → `GET /api/analysis/status`
- `POST /api/sectors/refresh` → `POST /api/analysis/refresh-sectors`

**New Slice 1B Endpoints:**
- `POST /api/analysis/theme-detection` - Trigger theme detection scan
- `GET /api/analysis/themes` - Get active themes
- `POST /api/analysis/temperature-monitor` - Start temperature monitoring
- `GET /api/analysis/temperature/{sector}` - Get sector temperature

**Implementation Steps:**
1. Create `analysis.py` router file
2. Move analysis-related endpoints from `sectors.py`
3. Update service imports and dependencies
4. Add new Slice 1B analysis endpoints
5. Update main.py to include new router

#### 1.2 Update Sectors Router
**File:** `backend/api/routes/sectors.py` (refactored)

**Remaining Endpoints:**
- `GET /api/sectors` - Get all sector sentiment data
- `GET /api/sectors/{sector_name}` - Get sector details
- `GET /api/sectors/{sector_name}/stocks` - Get sector stocks
- `GET /api/sectors/{sector_name}/themes` - Get themes affecting sector

**Changes:**
- Remove analysis-related endpoints
- Add theme integration endpoints
- Simplify sector display logic
- Focus on sentiment and display only

### Phase 2: Cache Management Centralization

#### 2.1 Create New Cache Router
**File:** `backend/api/routes/cache.py`

**Endpoints to Move:**
- `GET /api/sectors/cache/stats` → `GET /api/cache/stats`
- `DELETE /api/sectors/cache` → `DELETE /api/cache/clear`

**New Cache Endpoints:**
- `GET /api/cache/health` - Cache system health
- `POST /api/cache/warm` - Warm cache with fresh data
- `GET /api/cache/keys` - List cached keys
- `DELETE /api/cache/{key}` - Clear specific cache key

**Implementation Steps:**
1. Create `cache.py` router file
2. Move cache-related endpoints from `sectors.py`
3. Enhance cache service with new endpoints
4. Add cache performance monitoring
5. Update main.py to include cache router

#### 2.2 Update Cache Service
**File:** `backend/services/cache_service.py` (enhanced)

**New Features:**
- Cache key management
- Cache warming strategies
- Performance metrics
- Cache invalidation patterns
- Multi-level caching (Redis + memory)

### Phase 3: Slice 1B Intelligence Integration

#### 3.1 Theme Detection Integration
**New Endpoints in Analysis Router:**
- `GET /api/analysis/themes/active` - Get currently active themes
- `POST /api/analysis/themes/scan` - Trigger theme detection scan
- `GET /api/analysis/themes/{theme_id}` - Get specific theme details
- `GET /api/analysis/themes/{theme_id}/stocks` - Get stocks affected by theme

#### 3.2 Temperature Monitoring Integration
**New Endpoints in Analysis Router:**
- `GET /api/analysis/temperature` - Get all sector temperatures
- `GET /api/analysis/temperature/{sector}` - Get sector temperature
- `POST /api/analysis/temperature/monitor` - Start temperature monitoring
- `GET /api/analysis/temperature/alerts` - Get temperature alerts

#### 3.3 Sympathy Network Integration
**New Endpoints in Analysis Router:**
- `GET /api/analysis/sympathy/{symbol}` - Get sympathy network for symbol
- `POST /api/analysis/sympathy/update` - Update sympathy networks
- `GET /api/analysis/sympathy/alerts` - Get sympathy alerts

### Phase 4: Enhanced Error Handling and Monitoring

#### 4.1 Analysis Error Handling
- Analysis timeout handling
- Partial analysis completion
- Error recovery mechanisms
- Progress tracking for long-running analysis

#### 4.2 Cache Error Handling
- Cache miss handling
- Cache corruption recovery
- Fallback strategies
- Performance degradation handling

#### 4.3 Monitoring Integration
- Analysis performance metrics
- Cache hit/miss ratios
- API response times
- Error rate tracking

---

## 📋 Implementation Checklist

### Phase 1: Analysis Engine Extraction
- [ ] Create `backend/api/routes/analysis.py`
- [ ] Move analysis endpoints from `sectors.py`
- [ ] Update `sectors.py` to remove analysis logic
- [ ] Update `main.py` to include analysis router
- [ ] Update service imports and dependencies
- [ ] Test all moved endpoints
- [ ] Update API documentation

### Phase 2: Cache Management Centralization
- [ ] Create `backend/api/routes/cache.py`
- [ ] Move cache endpoints from `sectors.py`
- [ ] Enhance cache service with new features
- [ ] Update `main.py` to include cache router
- [ ] Test cache management endpoints
- [ ] Update cache service documentation

### Phase 3: Slice 1B Intelligence Integration
- [ ] Add theme detection endpoints to analysis router
- [ ] Add temperature monitoring endpoints
- [ ] Add sympathy network endpoints
- [ ] Update sector router with theme integration
- [ ] Test new intelligence endpoints
- [ ] Update API documentation for new features

### Phase 4: Enhanced Error Handling
- [ ] Implement analysis error handling
- [ ] Implement cache error handling
- [ ] Add monitoring and metrics
- [ ] Test error scenarios
- [ ] Update error documentation

---

## 🔧 Technical Implementation Details

### Router Structure
```python
# backend/api/routes/analysis.py
router = APIRouter(prefix="/analysis", tags=["analysis"])

# backend/api/routes/cache.py
router = APIRouter(prefix="/cache", tags=["cache"])

# Updated main.py
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(sectors.router, prefix="/api", tags=["sectors"])
app.include_router(stocks.router, prefix="/api", tags=["stocks"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(cache.router, prefix="/api", tags=["cache"])
```

### Service Dependencies
```python
# Analysis router dependencies
from services.analysis_scheduler import get_analysis_scheduler
from services.theme_detection import get_theme_detector
from services.temperature_monitor import get_temperature_monitor

# Cache router dependencies
from services.cache_service import get_cache_service
from services.performance_monitor import get_performance_monitor
```

### Database Models
```python
# New models for Slice 1B
from models.theme_detection import ThemeDetection
from models.temperature_monitoring import TemperatureData
from models.sympathy_network import SympathyNetwork
```

---

## 🧪 Testing Strategy

### Unit Testing
- Test each router independently
- Mock service dependencies
- Test error handling scenarios
- Validate endpoint responses

### Integration Testing
- Test router interactions
- Test service integration
- Test database operations
- Test cache operations

### End-to-End Testing
- Test complete analysis workflow
- Test cache management workflow
- Test theme detection workflow
- Test temperature monitoring workflow

---

## 📈 Migration Strategy

### Backward Compatibility
- Keep existing endpoint URLs working
- Add deprecation warnings for old endpoints
- Provide migration guide for frontend
- Maintain API versioning

### Gradual Migration
- Phase 1: Extract analysis engine
- Phase 2: Centralize cache management
- Phase 3: Add Slice 1B features
- Phase 4: Enhance error handling

### Rollback Plan
- Keep old router files as backup
- Maintain feature flags for new endpoints
- Document rollback procedures
- Test rollback scenarios

---

## 🎯 Success Metrics

### Performance Metrics
- API response times remain <1 second for cached data
- Analysis completion times remain <5 minutes
- Cache hit rates >90%
- Error rates <1%

### Functionality Metrics
- All existing endpoints continue working
- New Slice 1B endpoints function correctly
- Analysis engine operates independently
- Cache management is system-wide

### Maintainability Metrics
- Code complexity reduced
- Test coverage increased
- Documentation completeness
- Developer productivity improved

---

## ⚠️ Risk Mitigation

### Technical Risks
- **Breaking Changes:** Maintain backward compatibility
- **Performance Degradation:** Monitor response times
- **Data Loss:** Implement proper backup strategies
- **Service Dependencies:** Add circuit breakers

### Operational Risks
- **Deployment Issues:** Use feature flags
- **Rollback Complexity:** Maintain simple rollback procedures
- **Testing Coverage:** Ensure comprehensive testing
- **Documentation:** Keep documentation updated

---

## 📅 Implementation Timeline

### Week 1: Analysis Engine Extraction
- Day 1-2: Create analysis router
- Day 3-4: Move analysis endpoints
- Day 5: Update dependencies and test

### Week 2: Cache Management Centralization
- Day 1-2: Create cache router
- Day 3-4: Move cache endpoints
- Day 5: Enhance cache service and test

### Week 3: Slice 1B Intelligence Integration
- Day 1-2: Add theme detection endpoints
- Day 3-4: Add temperature monitoring endpoints
- Day 5: Add sympathy network endpoints

### Week 4: Enhanced Error Handling
- Day 1-2: Implement error handling
- Day 3-4: Add monitoring and metrics
- Day 5: Comprehensive testing and documentation

---

This refactoring plan provides a clear roadmap for optimizing the API structure for Slice 1B intelligence features while maintaining backward compatibility and ensuring comprehensive testing coverage. 