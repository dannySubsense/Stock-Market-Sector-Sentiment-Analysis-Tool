clear
# FMP Universe Integration Plan - Complete Implementation Strategy

## Overview
**Objective**: Replace failing dual-API approach with single FMP stock screener call + 1:1 sector mapping

**Current Problem**: Universe count = 0 due to FMP rate limiting on free tier
**Solution**: Single unlimited FMP screener call + ultra-simple 1:1 sector mapping

**MAJOR SIMPLIFICATION**: Direct 1:1 mapping of FMP's 11 sectors + 1 theme slot placeholder (no complex discovery needed)

---

## Core Requirements Alignment

### SDD Framework Preservation ✅
- **Maintain 8 Core Sectors**: Technology, Healthcare, Energy, Financial, Consumer Discretionary, Industrials, Materials, Utilities
- **Multi-Timeframe Analysis**: 30min, 1D, 3D, 1W (unchanged)
- **Stock Rankings**: Top 3 bullish/bearish per sector (unchanged)
- **Target Universe**: 1,200-1,500 small-cap stocks

### Enhanced Capabilities 🚀
- **1:1 FMP Sector Mapping**: Direct mapping of FMP's 11 professional sectors
- **Theme Slot Placeholder**: Slot 12 reserved for hot theme tracking (Bitcoin Treasury, AI, etc.)
- **Single API Call**: 99.97% reduction in API calls (3,000+ → 1)
- **Processing Speed**: <30 seconds target vs 10+ minutes current
- **Ultra-Simple Architecture**: No complex classification algorithms needed

---

## Implementation Strategy

### Phase 1: Enhanced FMP Client (Week 1)
**Target**: Complete universe retrieval with unlimited screener call

#### Changes to `backend/mcp/fmp_client.py`

```python
async def get_stock_screener_complete(self) -> Dict[str, Any]:
    """
    Get complete small-cap universe using FMP stock screener
    NO LIMIT PARAMETER - retrieves entire qualifying universe
    
    Universe Criteria:
    - Market Cap: $10M - $2B
    - Price: $1.00 - $100.00  
    - Volume: 1M+ daily
    - Exchanges: NASDAQ, NYSE only
    - Active trading only
    """
    try:
        if not self.api_key:
            raise ValueError("No FMP API key configured")
        
        url = f"{self.base_url}/v3/stock-screener"
        params = {
            "marketCapMoreThan": 10_000_000,      # $10M minimum
            "marketCapLowerThan": 2_000_000_000,  # $2B maximum
            "exchange": "NASDAQ,NYSE",            # Valid exchanges only
            "volumeMoreThan": 1_000_000,          # 1M+ volume requirement
            "priceMoreThan": 1.00,                # Minimum price
            "priceLowerThan": 100.00,             # Maximum price
            "isActivelyTrading": True,            # Active stocks only
            "apikey": self.api_key
            # CRITICAL: NO LIMIT PARAMETER - get complete universe
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Log universe size for monitoring
        universe_size = len(data) if isinstance(data, list) else 0
        logger.info(f"FMP Screener returned {universe_size} stocks")
        
        return {
            "status": "success",
            "stocks": data if isinstance(data, list) else [],
            "universe_size": universe_size,
            "filters_applied": params,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"FMP stock screener failed: {e}")
        return {
            "status": "error", 
            "message": str(e),
            "stocks": [],
            "universe_size": 0
        }
```

### Phase 2: Dynamic Sector Discovery Engine (Week 1)
**Target**: Intelligent sector classification with auto-discovery capabilities

#### New Service: `backend/services/sector_discovery.py`

```python
"""
Dynamic Sector Discovery Engine
Handles intelligent sector mapping and discovery for expandable sector framework
"""

from typing import List, Dict, Any, Set, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from core.database import SessionLocal

logger = logging.getLogger(__name__)

class SectorDiscovery:
    """
    Dynamic sector discovery and mapping engine
    Processes FMP data → Discovers sectors → Maps to known/creates new → Stores
    """
    
    def __init__(self):
        # Core 8 sectors from SDD framework (never removed)
        self.core_sectors = {
            "technology", "healthcare", "energy", "financial",
            "consumer_discretionary", "industrials", "materials", "utilities"
        }
        
        # Sector mapping rules for intelligent classification
        self.sector_mapping_rules = {
            "technology": {
                "keywords": ["software", "technology", "ai", "artificial intelligence", 
                           "computer", "internet", "semiconductor", "tech", "data"],
                "industries": ["software development", "internet services", "semiconductors"]
            },
            "healthcare": {
                "keywords": ["healthcare", "biotech", "pharmaceutical", "medical", 
                           "drug", "therapeutics", "clinical", "pharma"],
                "industries": ["biotechnology", "pharmaceuticals", "medical devices"]
            },
            "energy": {
                "keywords": ["energy", "oil", "gas", "solar", "renewable", 
                           "mining", "coal", "petroleum", "power"],
                "industries": ["oil & gas", "renewable energy", "utilities"]
            },
            "financial": {
                "keywords": ["bank", "financial", "insurance", "credit", 
                           "lending", "fintech", "payment", "finance"],
                "industries": ["banking", "insurance", "financial services"]
            },
            "consumer_discretionary": {
                "keywords": ["retail", "consumer", "restaurant", "entertainment", 
                           "gaming", "media", "clothing", "leisure"],
                "industries": ["retail", "entertainment", "consumer services"]
            },
            "industrials": {
                "keywords": ["industrial", "manufacturing", "aerospace", "defense", 
                           "transportation", "logistics", "construction"],
                "industries": ["aerospace", "industrial manufacturing", "transportation"]
            },
            "materials": {
                "keywords": ["materials", "steel", "copper", "aluminum", 
                           "chemicals", "construction", "metals"],
                "industries": ["basic materials", "chemicals", "metals & mining"]
            },
            "utilities": {
                "keywords": ["utilities", "electric", "water", "gas", 
                           "power", "energy infrastructure"],
                "industries": ["electric utilities", "water utilities"]
            }
        }
        
        # Track discovered sectors for expansion
        self.discovered_sectors = set()
        self.sector_confidence_threshold = 0.7
    
    async def discover_and_map_sectors(self, fmp_stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main processing pipeline: FMP Data → Sector Discovery → Mapping → Storage
        
        Args:
            fmp_stocks: Raw stock data from FMP screener
            
        Returns:
            Dict containing classified stocks, discovered sectors, and distribution
        """
        logger.info(f"Starting sector discovery for {len(fmp_stocks)} stocks")
        
        classified_stocks = []
        discovered_new_sectors = set()
        unknown_classifications = []
        sector_distribution = {}
        
        for stock in fmp_stocks:
            try:
                # Extract sector information from FMP data
                fmp_sector = stock.get('sector', '').strip()
                fmp_industry = stock.get('industry', '').strip()
                company_name = stock.get('companyName', stock.get('name', '')).strip()
                
                # 1. Attempt mapping to core sectors
                mapped_result = self._map_to_core_sector(fmp_sector, fmp_industry, company_name)
                
                if mapped_result['mapped_sector']:
                    # Successfully mapped to core sector
                    sector = mapped_result['mapped_sector']
                    confidence = mapped_result['confidence']
                else:
                    # 2. Discover new sector or handle unknown
                    discovery_result = self._discover_new_sector(fmp_sector, fmp_industry)
                    sector = discovery_result['sector']
                    confidence = discovery_result['confidence']
                    
                    if discovery_result['is_new']:
                        discovered_new_sectors.add(sector)
                    
                    if confidence < self.sector_confidence_threshold:
                        unknown_classifications.append({
                            'symbol': stock.get('symbol'),
                            'fmp_sector': fmp_sector,
                            'fmp_industry': fmp_industry,
                            'suggested_sector': sector,
                            'confidence': confidence
                        })
                
                # 3. Create classified stock entry
                classified_stock = {
                    **stock,  # Preserve all original FMP data
                    'mapped_sector': sector,
                    'sector_confidence': confidence,
                    'original_fmp_sector': fmp_sector,
                    'original_fmp_industry': fmp_industry,
                    'classification_timestamp': datetime.utcnow().isoformat(),
                    'needs_review': confidence < self.sector_confidence_threshold
                }
                
                classified_stocks.append(classified_stock)
                
                # Update distribution tracking
                sector_distribution[sector] = sector_distribution.get(sector, 0) + 1
                
            except Exception as e:
                logger.warning(f"Error classifying stock {stock.get('symbol', 'unknown')}: {e}")
                # Add to unknown for manual review
                unknown_classifications.append({
                    'symbol': stock.get('symbol'),
                    'error': str(e),
                    'raw_data': stock
                })
                continue
        
        logger.info(f"Sector discovery completed: {len(classified_stocks)} classified, "
                   f"{len(discovered_new_sectors)} new sectors discovered")
        
        return {
            "status": "success",
            "classified_stocks": classified_stocks,
            "discovered_new_sectors": list(discovered_new_sectors),
            "sector_distribution": sector_distribution,
            "unknown_classifications": unknown_classifications,
            "total_processed": len(fmp_stocks),
            "classification_rate": len(classified_stocks) / len(fmp_stocks) * 100
        }
    
    def _map_to_core_sector(self, fmp_sector: str, fmp_industry: str, company_name: str) -> Dict[str, Any]:
        """
        Attempt to map FMP sector/industry data to core 8 sectors
        
        Returns:
            Dict with mapped_sector, confidence score, and reasoning
        """
        if not fmp_sector and not fmp_industry:
            return {"mapped_sector": None, "confidence": 0.0, "reason": "No sector data"}
        
        # Combine all text for keyword matching
        combined_text = f"{fmp_sector.lower()} {fmp_industry.lower()} {company_name.lower()}"
        
        best_match = None
        best_confidence = 0.0
        
        for sector, rules in self.sector_mapping_rules.items():
            confidence = 0.0
            matches = []
            
            # Check keyword matches
            for keyword in rules['keywords']:
                if keyword in combined_text:
                    confidence += 0.3  # Each keyword match adds confidence
                    matches.append(f"keyword:{keyword}")
            
            # Check industry exact matches (higher weight)
            for industry in rules.get('industries', []):
                if industry.lower() in fmp_industry.lower():
                    confidence += 0.5  # Industry matches are more reliable
                    matches.append(f"industry:{industry}")
            
            # Direct sector name match (highest weight)
            if sector in fmp_sector.lower() or fmp_sector.lower() in sector:
                confidence += 0.7
                matches.append(f"sector_match:{fmp_sector}")
            
            # Normalize confidence to 0-1 range
            confidence = min(confidence, 1.0)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = sector
        
        return {
            "mapped_sector": best_match if best_confidence >= 0.3 else None,
            "confidence": best_confidence,
            "reason": f"Best match: {best_match}" if best_match else "No sufficient match"
        }
    
    def _discover_new_sector(self, fmp_sector: str, fmp_industry: str) -> Dict[str, Any]:
        """
        Discover and create new sector classification for unmapped stocks
        
        Returns:
            Dict with sector name, confidence, and discovery metadata
        """
        # Generate new sector name from FMP data
        if fmp_sector:
            # Clean and normalize sector name
            new_sector = fmp_sector.lower().replace(' ', '_').replace('&', 'and')
            new_sector = ''.join(c for c in new_sector if c.isalnum() or c == '_')
            confidence = 0.8  # High confidence for direct FMP sector
            is_new = new_sector not in self.core_sectors
        elif fmp_industry:
            # Use industry as fallback
            new_sector = fmp_industry.lower().replace(' ', '_').replace('&', 'and')
            new_sector = ''.join(c for c in new_sector if c.isalnum() or c == '_')
            confidence = 0.6  # Medium confidence for industry-based
            is_new = True
        else:
            # Unknown classification
            new_sector = "unknown_sector"
            confidence = 0.1
            is_new = False
        
        # Track discovery
        if is_new and new_sector != "unknown_sector":
            self.discovered_sectors.add(new_sector)
        
        return {
            "sector": new_sector,
            "confidence": confidence,
            "is_new": is_new,
            "source": "fmp_sector" if fmp_sector else "fmp_industry" if fmp_industry else "unknown"
        }
    
    async def store_sector_mappings(self, discovery_result: Dict[str, Any]) -> Dict[str, Any]:
        """Store discovered sector mappings in database for future reference"""
        try:
            with SessionLocal() as db:
                stored_count = 0
                
                for stock in discovery_result['classified_stocks']:
                    # Store mapping if confidence is reasonable
                    if stock['sector_confidence'] >= 0.5:
                        # Check if mapping already exists
                        existing = db.execute("""
                            SELECT id FROM sector_mappings 
                            WHERE original_sector = %s AND original_industry = %s
                        """, (stock['original_fmp_sector'], stock['original_fmp_industry'])).fetchone()
                        
                        if not existing:
                            db.execute("""
                                INSERT INTO sector_mappings 
                                (original_sector, original_industry, mapped_sector, confidence_score, 
                                 is_core_sector, needs_review, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                stock['original_fmp_sector'],
                                stock['original_fmp_industry'], 
                                stock['mapped_sector'],
                                stock['sector_confidence'],
                                stock['mapped_sector'] in self.core_sectors,
                                stock['needs_review'],
                                datetime.utcnow()
                            ))
                            stored_count += 1
                
                db.commit()
                
                return {
                    "status": "success",
                    "mappings_stored": stored_count,
                    "new_sectors_discovered": len(discovery_result['discovered_new_sectors'])
                }
                
        except Exception as e:
            logger.error(f"Failed to store sector mappings: {e}")
            return {"status": "error", "message": str(e)}
```

### Phase 3: Database Schema Enhancement (Week 2)
**Target**: Flexible schema supporting dynamic sector expansion

#### New Table: Sector Mappings
```sql
-- Dynamic sector mapping table
CREATE TABLE IF NOT EXISTS sector_mappings (
    id SERIAL PRIMARY KEY,
    original_sector VARCHAR(100) NOT NULL,
    original_industry VARCHAR(100),
    mapped_sector VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    is_core_sector BOOLEAN DEFAULT FALSE,
    needs_review BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    reviewed_by VARCHAR(50),
    review_notes TEXT,
    
    -- Indexing for performance
    INDEX idx_original_sector (original_sector),
    INDEX idx_mapped_sector (mapped_sector),
    INDEX idx_needs_review (needs_review),
    
    -- Ensure unique mappings
    UNIQUE KEY unique_mapping (original_sector, original_industry)
);

-- Sector statistics tracking
CREATE TABLE IF NOT EXISTS sector_stats (
    id SERIAL PRIMARY KEY,
    sector_name VARCHAR(50) NOT NULL,
    stock_count INTEGER DEFAULT 0,
    avg_market_cap DECIMAL(15,2),
    total_volume BIGINT,
    last_updated TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_sector_name (sector_name),
    UNIQUE KEY unique_sector (sector_name)
);
```

#### Enhanced Stock Universe Table
```sql
-- Add dynamic sector support to existing table
ALTER TABLE stock_universe 
ADD COLUMN IF NOT EXISTS original_fmp_sector VARCHAR(100),
ADD COLUMN IF NOT EXISTS original_fmp_industry VARCHAR(100),
ADD COLUMN IF NOT EXISTS sector_confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS needs_sector_review BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS sector_classification_date TIMESTAMP;

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_original_fmp_sector ON stock_universe(original_fmp_sector);
CREATE INDEX IF NOT EXISTS idx_sector_confidence ON stock_universe(sector_confidence);
CREATE INDEX IF NOT EXISTS idx_needs_review ON stock_universe(needs_sector_review);
```

### Phase 4: Complete Pipeline Integration (Week 2)
**Target**: End-to-end FMP → Discovery → Storage pipeline

#### Updated `backend/services/universe_builder.py`

```python
async def build_daily_universe(self) -> Dict[str, Any]:
    """
    Complete daily universe build with FMP + dynamic sector discovery
    Single API call approach with intelligent sector mapping
    """
    try:
        logger.info("Starting FMP-based universe build with sector discovery")
        
        # Step 1: Get complete universe from FMP (single unlimited call)
        logger.info("Step 1/4: Fetching complete universe from FMP")
        fmp_result = await self.fmp_client.get_stock_screener_complete()
        
        if fmp_result["status"] != "success":
            raise Exception(f"FMP screener failed: {fmp_result.get('message', 'Unknown error')}")
        
        raw_stocks = fmp_result["stocks"]
        logger.info(f"FMP returned {len(raw_stocks)} qualifying stocks")
        
        # Step 2: Dynamic sector discovery and mapping
        logger.info("Step 2/4: Processing sector discovery and mapping")
        sector_discovery = SectorDiscovery()
        discovery_result = await sector_discovery.discover_and_map_sectors(raw_stocks)
        
        if discovery_result["status"] != "success":
            raise Exception("Sector discovery failed")
        
        classified_stocks = discovery_result["classified_stocks"]
        logger.info(f"Classified {len(classified_stocks)} stocks into {len(discovery_result['sector_distribution'])} sectors")
        
        # Step 3: Store sector mappings for future reference
        logger.info("Step 3/4: Storing sector mappings")
        mapping_result = await sector_discovery.store_sector_mappings(discovery_result)
        
        # Step 4: Update stock universe table
        logger.info("Step 4/4: Updating stock universe database")
        update_result = await self._update_stock_universe_with_sectors(classified_stocks)
        
        # Final statistics
        final_result = {
            "status": "success",
            "universe_size": len(classified_stocks),
            "sectors": discovery_result["sector_distribution"],
            "discovered_new_sectors": discovery_result["discovered_new_sectors"],
            "classification_rate": discovery_result["classification_rate"],
            "unknown_classifications": len(discovery_result["unknown_classifications"]),
            "update_result": update_result,
            "mapping_result": mapping_result,
            "timestamp": datetime.utcnow().isoformat(),
            "processing_summary": {
                "fmp_stocks_retrieved": len(raw_stocks),
                "stocks_classified": len(classified_stocks),
                "sectors_mapped": len(discovery_result["sector_distribution"]),
                "new_sectors_found": len(discovery_result["discovered_new_sectors"])
            }
        }
        
        logger.info(f"Universe build completed successfully: {final_result['universe_size']} stocks in {len(final_result['sectors'])} sectors")
        return final_result
        
    except Exception as e:
        logger.error(f"Universe build failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "universe_size": 0,
            "sectors": {},
            "timestamp": datetime.utcnow().isoformat()
        }

async def _update_stock_universe_with_sectors(self, classified_stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Update stock universe table with sector-classified stocks"""
    try:
        with SessionLocal() as db:
            # Mark all existing stocks as inactive
            db.query(StockUniverse).update({"is_active": False})
            
            updated_count = 0
            created_count = 0
            
            for stock_data in classified_stocks:
                existing_stock = (
                    db.query(StockUniverse)
                    .filter(StockUniverse.symbol == stock_data["symbol"])
                    .first()
                )
                
                if existing_stock:
                    # Update existing stock with new sector data
                    existing_stock.company_name = stock_data.get("companyName", stock_data.get("name"))
                    existing_stock.exchange = stock_data.get("exchange")
                    existing_stock.market_cap = stock_data.get("marketCap", 0)
                    existing_stock.current_price = stock_data.get("price", 0)
                    existing_stock.avg_daily_volume = stock_data.get("avgVolume", 0)
                    existing_stock.sector = stock_data["mapped_sector"]
                    existing_stock.original_fmp_sector = stock_data["original_fmp_sector"]
                    existing_stock.original_fmp_industry = stock_data["original_fmp_industry"]
                    existing_stock.sector_confidence = stock_data["sector_confidence"]
                    existing_stock.needs_sector_review = stock_data["needs_review"]
                    existing_stock.sector_classification_date = datetime.utcnow()
                    existing_stock.is_active = True
                    existing_stock.last_updated = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new stock entry
                    new_stock = StockUniverse(
                        symbol=stock_data["symbol"],
                        company_name=stock_data.get("companyName", stock_data.get("name")),
                        exchange=stock_data.get("exchange"),
                        market_cap=stock_data.get("marketCap", 0),
                        current_price=stock_data.get("price", 0),
                        avg_daily_volume=stock_data.get("avgVolume", 0),
                        sector=stock_data["mapped_sector"],
                        original_fmp_sector=stock_data["original_fmp_sector"],
                        original_fmp_industry=stock_data["original_fmp_industry"],
                        sector_confidence=stock_data["sector_confidence"],
                        needs_sector_review=stock_data["needs_review"],
                        sector_classification_date=datetime.utcnow(),
                        is_active=True,
                        last_updated=datetime.utcnow()
                    )
                    db.add(new_stock)
                    created_count += 1
            
            db.commit()
            
            # Count inactive stocks
            inactive_count = db.query(StockUniverse).filter(StockUniverse.is_active == False).count()
            
            return {
                "status": "success",
                "updated": updated_count,
                "created": created_count,
                "inactive": inactive_count,
                "total_active": len(classified_stocks)
            }
            
    except Exception as e:
        logger.error(f"Failed to update stock universe: {e}")
        return {"status": "error", "message": str(e)}
```

---

## Expected Results

### API Performance Improvement
| Metric | Before (Dual API) | After (FMP Single) | Improvement |
|--------|------------------|-------------------|-------------|
| **API Calls** | 3,000+ calls | **1 call** | 99.97% reduction |
| **Processing Time** | 10+ minutes | **<30 seconds** | 95% faster |
| **Success Rate** | 0% (rate limited) | **>95%** | ✅ Fixed |
| **Universe Size** | 0 stocks | **~1,500 stocks** | Target achieved |

### Sector Discovery Capabilities
- ✅ **Core 8 Sectors**: Maintained from SDD framework
- 🚀 **Dynamic Discovery**: Auto-detect emerging sectors (AI, Fintech, Renewable Energy)
- 📊 **Confidence Scoring**: Track classification reliability
- 🔍 **Manual Review Queue**: Flag uncertain classifications
- 📈 **Expandable Schema**: Handle future market evolution

### Database Architecture
- ✅ **Flexible Schema**: Supports sector expansion
- ✅ **Original Data Preservation**: FMP sector/industry data retained
- ✅ **Confidence Tracking**: Monitor classification quality
- ✅ **Review Workflow**: Manual oversight for edge cases

---

## Development Workflow

### Week 1 Tasks
1. **Day 1-2**: Implement enhanced FMP client with unlimited screener
2. **Day 3-4**: Build sector discovery engine
3. **Day 5**: Integration testing and validation

### Week 2 Tasks  
1. **Day 1-2**: Database schema updates and migrations
2. **Day 3-4**: Complete pipeline integration
3. **Day 5**: Performance testing and optimization

### Success Criteria
- ✅ Universe size reaches 1,200-1,500 stocks
- ✅ Processing time under 30 seconds
- ✅ Sector distribution reasonable across 8+ sectors
- ✅ Classification confidence >80% average
- ✅ Manual review queue <10% of stocks

---

## Risk Mitigation

### Technical Risks
- **FMP API Changes**: Monitor API stability, maintain Polygon.io as backup
- **Sector Classification Accuracy**: Implement confidence thresholds and review queues
- **Database Performance**: Index optimization for sector queries

### Business Risks  
- **Sector Evolution**: Dynamic discovery handles new market sectors
- **Data Quality**: Original FMP data preserved for validation
- **Scalability**: Single API call approach eliminates rate limiting

---

## Future Enhancements

### Phase 5: Advanced Analytics (Future)
- **Sector Correlation Analysis**: Track inter-sector relationships
- **Emerging Sector Detection**: AI-based sector trend identification  
- **Custom Sector Creation**: User-defined sector groupings

### Phase 6: Performance Optimization (Future)
- **Caching Strategy**: Redis-based sector classification cache
- **Incremental Updates**: Only refresh changed data
- **Parallel Processing**: Multi-threaded sector discovery

---

## Monitoring & Validation

### Key Metrics to Track
- **Universe Size Stability**: Target 1,200-1,500 stocks
- **Sector Distribution**: Reasonable balance across sectors
- **Classification Confidence**: Average >80%
- **Processing Performance**: <30 seconds target
- **Manual Review Rate**: <10% of classifications

### Alerting Thresholds
- Universe size <1,000 or >2,000 stocks
- Average confidence score <70%
- Processing time >60 seconds
- Manual review rate >15%

This comprehensive plan ensures reliable universe building while maintaining SDD architecture integrity and enabling future sector expansion capabilities. 