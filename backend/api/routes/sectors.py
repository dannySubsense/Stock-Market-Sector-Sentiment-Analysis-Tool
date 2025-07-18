"""
Sectors API endpoints for the 8-sector grid dashboard
Enhanced with cache integration and on-demand analysis for Slice 1A
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from core.database import get_db
from models.sector_sentiment import SectorSentiment
from models.stock_data import StockData
from services.cache_service import get_cache_service
from services.analysis_scheduler import get_analysis_scheduler
from services.sector_calculator import get_sector_calculator
from services.stock_ranker import get_stock_ranker

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/sectors")
async def get_all_sectors(
    use_cache: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all sector sentiment data for the main dashboard
    Enhanced with Redis caching for sub-1-second response times
    """
    try:
        # Try cache first if enabled
        if use_cache:
            try:
                cache_service = get_cache_service()
                cached_data = await cache_service.get_cached_all_sectors()
                
                if cached_data:
                    logger.debug("Returning cached sector data")
                    return {
                        "sectors": cached_data.get("sectors", {}),
                        "timestamp": cached_data.get("cached_at"),
                        "total_sectors": len(cached_data.get("sectors", {})),
                        "source": "cache",
                        "cache_ttl": cached_data.get("cache_ttl")
                    }
            except Exception as e:
                logger.warning(f"Cache lookup failed, falling back to database: {e}")
        
        # Fallback to database
        sectors = db.query(SectorSentiment).all()
        
        if not sectors:
            # Return default sectors if none exist
            default_data = get_default_sectors()
            # Cache the default data
            if use_cache:
                try:
                    cache_service = get_cache_service()
                    await cache_service.cache_all_sectors(default_data["sectors"])
                except Exception as e:
                    logger.warning(f"Failed to cache default sectors: {e}")
            return default_data
        
        # Format sectors for frontend
        sector_data = {}
        for sector in sectors:
            # Get top stocks for this sector
            top_stocks = await _get_sector_top_stocks(sector.sector, db)
            
            sector_info = {
                "sector": sector.sector,
                "sentiment_score": float(sector.sentiment_score) if sector.sentiment_score else 0.0,
                "color_classification": sector.color_classification,
                "confidence_level": float(sector.confidence_level) if sector.confidence_level else 0.5,
                "trading_signal": _get_trading_signal_from_color(sector.color_classification),
                "timeframe_scores": {
                    "30min": float(sector.timeframe_30min) if sector.timeframe_30min else 0.0,
                    "1day": float(sector.timeframe_1day) if sector.timeframe_1day else 0.0,
                    "3day": float(sector.timeframe_3day) if sector.timeframe_3day else 0.0,
                    "1week": float(sector.timeframe_1week) if sector.timeframe_1week else 0.0
                },
                "last_updated": sector.last_updated.isoformat() if sector.last_updated else datetime.utcnow().isoformat(),
                "stock_count": len(top_stocks.get("all_stocks", [])),
                "top_bullish": top_stocks.get("top_bullish", []),
                "top_bearish": top_stocks.get("top_bearish", [])
            }
            sector_data[sector.sector] = sector_info
        
        result = {
            "sectors": sector_data,
            "timestamp": datetime.utcnow().isoformat(),
            "total_sectors": len(sector_data),
            "source": "database"
        }
        
        # Cache the result
        if use_cache:
            try:
                cache_service = get_cache_service()
                await cache_service.cache_all_sectors(sector_data)
                logger.debug("Cached fresh sector data")
            except Exception as e:
                logger.warning(f"Failed to cache sector data: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get sectors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sectors: {str(e)}")

async def _get_sector_top_stocks(sector: str, db: Session) -> Dict[str, Any]:
    """Helper function to get top stocks for a sector"""
    try:
        # Get stocks with rankings for this sector
        bullish_stocks = db.query(StockData).filter(
            StockData.sector == sector,
            StockData.bullish_rank.isnot(None)
        ).order_by(StockData.bullish_rank).limit(3).all()
        
        bearish_stocks = db.query(StockData).filter(
            StockData.sector == sector,
            StockData.bearish_rank.isnot(None)
        ).order_by(StockData.bearish_rank).limit(3).all()
        
        all_stocks = db.query(StockData).filter(StockData.sector == sector).all()
        
        return {
            "top_bullish": [
                {
                    "symbol": stock.symbol,
                    "change_percent": float(stock.price_change_percent) if stock.price_change_percent else 0.0,
                    "volume_ratio": float(stock.volume) / float(stock.avg_daily_volume) if stock.avg_daily_volume else 1.0
                }
                for stock in bullish_stocks
            ],
            "top_bearish": [
                {
                    "symbol": stock.symbol,
                    "change_percent": float(stock.price_change_percent) if stock.price_change_percent else 0.0,
                    "volume_ratio": float(stock.volume) / float(stock.avg_daily_volume) if stock.avg_daily_volume else 1.0
                }
                for stock in bearish_stocks
            ],
            "all_stocks": all_stocks
        }
    except Exception as e:
        logger.warning(f"Failed to get top stocks for {sector}: {e}")
        return {"top_bullish": [], "top_bearish": [], "all_stocks": []}

def _get_trading_signal_from_color(color_classification: str) -> str:
    """Convert color classification to trading signal"""
    signal_mapping = {
        "dark_red": "PRIME_SHORTING_ENVIRONMENT",
        "light_red": "GOOD_SHORTING_ENVIRONMENT",
        "blue_neutral": "NEUTRAL_CAUTIOUS",
        "light_green": "AVOID_SHORTS",
        "dark_green": "DO_NOT_SHORT"
    }
    return signal_mapping.get(color_classification, "NEUTRAL_CAUTIOUS")

@router.get("/sectors/{sector_name}")
async def get_sector_details(sector_name: str, db: Session = Depends(get_db)):
    """Get detailed information for a specific sector"""
    try:
        # Get sector sentiment
        sector = db.query(SectorSentiment).filter(SectorSentiment.sector == sector_name).first()
        
        if not sector:
            raise HTTPException(status_code=404, detail=f"Sector '{sector_name}' not found")
        
        # Get top stocks for this sector
        top_stocks = db.query(StockData).filter(StockData.sector == sector_name).all()
        
        # Format bullish and bearish stocks
        bullish_stocks = []
        bearish_stocks = []
        
        for stock in top_stocks:
            stock_data = stock.get_display_data()
            if stock.price_change_percent > 0:
                bullish_stocks.append(stock_data)
            else:
                bearish_stocks.append(stock_data)
        
        # Sort by performance
        bullish_stocks.sort(key=lambda x: x["price_change_percent"], reverse=True)
        bearish_stocks.sort(key=lambda x: x["price_change_percent"])
        
        return {
            "sector": sector_name,
            "sentiment": {
                "score": sector.sentiment_score,
                "color": sector.color_classification,
                "confidence": sector.confidence_level,
                "trading_signal": sector.trading_signal,
                "description": sector.sentiment_description
            },
            "timeframes": sector.get_timeframe_summary(),
            "top_stocks": {
                "bullish": bullish_stocks[:3],  # Top 3 bullish
                "bearish": bearish_stocks[:3]   # Top 3 bearish
            },
            "last_updated": sector.last_updated.isoformat() if sector.last_updated else None,
            "is_stale": sector.is_stale
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sector details: {str(e)}")

@router.post("/sectors/refresh")
async def refresh_sector_analysis(db: Session = Depends(get_db)):
    """
    Trigger on-demand sector analysis refresh
    NOTE: This endpoint is deprecated. Use /api/analysis/refresh-sectors instead.
    """
    try:
        # Redirect to new analysis endpoint
        return {
            "message": "This endpoint is deprecated. Use /api/analysis/refresh-sectors instead.",
            "status": "deprecated",
            "redirect": "/api/analysis/refresh-sectors",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh sectors: {str(e)}")

@router.get("/sectors/{sector_name}/stocks")
async def get_sector_stocks(sector_name: str, db: Session = Depends(get_db)):
    """Get all stocks in a specific sector"""
    try:
        stocks = db.query(StockData).filter(StockData.sector == sector_name).all()
        
        if not stocks:
            return {
                "sector": sector_name,
                "stocks": [],
                "count": 0,
                "message": f"No stocks found for sector '{sector_name}'"
            }
        
        # Format stocks for response
        stock_data = []
        for stock in stocks:
            stock_info = stock.get_display_data()
            stock_data.append(stock_info)
        
        # Sort by performance (descending)
        stock_data.sort(key=lambda x: x["price_change_percent"], reverse=True)
        
        return {
            "sector": sector_name,
            "stocks": stock_data,
            "count": len(stock_data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sector stocks: {str(e)}")

def get_default_sectors() -> Dict[str, Any]:
    """Return default sector data when no sectors exist in database"""
    default_sectors = [
        "technology", "healthcare", "energy", "financial", 
        "consumer_discretionary", "industrials", "materials", "utilities"
    ]
    
    sector_data = {}
    for sector in default_sectors:
        sector_data[sector] = {
            "sector": sector,
            "sentiment_score": 0.0,
            "color_classification": "blue_neutral",
            "confidence_level": 0.5,
            "trading_signal": "NEUTRAL_CAUTIOUS",
            "timeframe_scores": {
                "30min": 0.0,
                "1day": 0.0,
                "3day": 0.0,
                "1week": 0.0
            },
            "last_updated": datetime.utcnow().isoformat(),
            "stock_count": 0,
            "top_bullish": [],
            "top_bearish": []
        }
    
    return {
        "sectors": sector_data,
        "timestamp": datetime.utcnow().isoformat(),
        "total_sectors": len(sector_data),
        "source": "default"
    }


# DEPRECATED: These endpoints have been moved to dedicated routers
# Use /api/analysis/on-demand instead of /api/sectors/analysis/on-demand
# Use /api/analysis/status instead of /api/sectors/analysis/status  
# Use /api/cache/stats instead of /api/sectors/cache/stats
# Use /api/cache/clear instead of /api/sectors/cache 