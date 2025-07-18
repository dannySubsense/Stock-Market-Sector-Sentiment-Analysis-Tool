"""
Stocks API endpoints for individual stock data and universe management
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.database import get_db
from models.stock_universe import StockUniverse
from models.stock_data import StockData

router = APIRouter()

@router.get("/stocks")
async def get_all_stocks(
    sector: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all stocks in the universe with optional filtering"""
    try:
        query = db.query(StockUniverse)
        
        # Filter by sector if provided
        if sector:
            query = query.filter(StockUniverse.sector == sector)
        
        # Filter only active stocks
        query = query.filter(StockUniverse.is_active == True)
        
        # Apply pagination
        stocks = query.offset(skip).limit(limit).all()
        
        # Get total count
        total_count = query.count()
        
        # Format stocks for response
        stock_data = []
        for stock in stocks:
            stock_info = {
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "sector": stock.sector,
                "market_cap": stock.market_cap,
                "market_cap_formatted": stock.market_cap_formatted,
                "current_price": stock.current_price,
                "avg_daily_volume": stock.avg_daily_volume,
                "volatility_multiplier": stock.volatility_multiplier,
                "gap_frequency": stock.gap_frequency,
                "shortability_score": stock.shortability_score,
                "exchange": stock.exchange,
                "is_micro_cap": stock.is_micro_cap,
                "is_small_cap": stock.is_small_cap,
                "last_updated": stock.last_updated.isoformat() if stock.last_updated else None
            }
            stock_data.append(stock_info)
        
        return {
            "stocks": stock_data,
            "total_count": total_count,
            "returned_count": len(stock_data),
            "skip": skip,
            "limit": limit,
            "sector_filter": sector,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stocks: {str(e)}")

@router.get("/stocks/{symbol}")
async def get_stock_details(symbol: str, db: Session = Depends(get_db)):
    """Get detailed information for a specific stock"""
    try:
        # Get stock from universe
        stock = db.query(StockUniverse).filter(StockUniverse.symbol == symbol.upper()).first()
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found in universe")
        
        # Get current stock data
        stock_data = db.query(StockData).filter(StockData.symbol == symbol.upper()).first()
        
        # Format response
        response = {
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "sector": stock.sector,
            "exchange": stock.exchange,
            "universe_info": {
                "market_cap": stock.market_cap,
                "market_cap_formatted": stock.market_cap_formatted,
                "avg_daily_volume": stock.avg_daily_volume,
                "volatility_multiplier": stock.volatility_multiplier,
                "gap_frequency": stock.gap_frequency,
                "shortability_score": stock.shortability_score,
                "is_micro_cap": stock.is_micro_cap,
                "is_small_cap": stock.is_small_cap,
                "meets_criteria": stock.should_include_in_universe()
            },
            "current_data": None,
            "last_updated": stock.last_updated.isoformat() if stock.last_updated else None
        }
        
        # Add current price data if available
        if stock_data:
            response["current_data"] = stock_data.get_display_data()
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stock details: {str(e)}")

@router.get("/stocks/universe/stats")
async def get_universe_stats(db: Session = Depends(get_db)):
    """Get statistics about the current stock universe"""
    try:
        # Get total counts
        total_stocks = db.query(StockUniverse).filter(StockUniverse.is_active == True).count()
        
        # Get sector breakdown
        sector_stats = db.query(
            StockUniverse.sector,
            func.count(StockUniverse.symbol).label('count')
        ).filter(
            StockUniverse.is_active == True
        ).group_by(StockUniverse.sector).all()
        
        # Get market cap breakdown
        micro_cap_count = db.query(StockUniverse).filter(
            StockUniverse.is_active == True,
            StockUniverse.market_cap < 300_000_000
        ).count()
        
        small_cap_count = db.query(StockUniverse).filter(
            StockUniverse.is_active == True,
            StockUniverse.market_cap >= 300_000_000,
            StockUniverse.market_cap <= 2_000_000_000
        ).count()
        
        # Get exchange breakdown
        exchange_stats = db.query(
            StockUniverse.exchange,
            func.count(StockUniverse.symbol).label('count')
        ).filter(
            StockUniverse.is_active == True
        ).group_by(StockUniverse.exchange).all()
        
        # Format sector stats
        sector_breakdown = {stat.sector: stat.count for stat in sector_stats}
        
        # Format exchange stats
        exchange_breakdown = {stat.exchange: stat.count for stat in exchange_stats}
        
        return {
            "total_stocks": total_stocks,
            "target_universe_size": 1500,
            "coverage_percentage": (total_stocks / 1500) * 100 if total_stocks else 0,
            "market_cap_breakdown": {
                "micro_cap": micro_cap_count,
                "small_cap": small_cap_count
            },
            "sector_breakdown": sector_breakdown,
            "exchange_breakdown": exchange_breakdown,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get universe stats: {str(e)}")

@router.get("/stocks/gaps")
async def get_gap_stocks(
    gap_type: str = Query("all", pattern="^(all|large|extreme)$"),
    db: Session = Depends(get_db)
):
    """Get stocks with significant gaps"""
    try:
        # Get stocks with gap data
        query = db.query(StockData).filter(
            StockData.gap_percent.isnot(None)
        )
        
        # Filter by gap type
        if gap_type == "large":
            query = query.filter(func.abs(StockData.gap_percent) >= 0.15)
        elif gap_type == "extreme":
            query = query.filter(func.abs(StockData.gap_percent) >= 0.30)
        
        # Get stocks and sort by gap size
        stocks = query.all()
        
        # Format response
        gap_stocks = []
        for stock in stocks:
            stock_data = stock.get_display_data()
            gap_stocks.append(stock_data)
        
        # Sort by absolute gap percentage (descending)
        gap_stocks.sort(key=lambda x: abs(x.get("gap_percent", 0)), reverse=True)
        
        return {
            "gap_stocks": gap_stocks,
            "count": len(gap_stocks),
            "gap_type": gap_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get gap stocks: {str(e)}")

@router.get("/stocks/volume-leaders")
async def get_volume_leaders(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get stocks with highest volume ratios"""
    try:
        # Get stocks with volume data, sorted by volume ratio
        stocks = db.query(StockData).filter(
            StockData.volume_ratio.isnot(None),
            StockData.volume_ratio > 1.0
        ).order_by(StockData.volume_ratio.desc()).limit(limit).all()
        
        # Format response
        volume_leaders = []
        for stock in stocks:
            stock_data = stock.get_display_data()
            volume_leaders.append(stock_data)
        
        return {
            "volume_leaders": volume_leaders,
            "count": len(volume_leaders),
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get volume leaders: {str(e)}")

@router.post("/stocks/universe/refresh")
async def refresh_universe(db: Session = Depends(get_db)):
    """Trigger universe refresh (placeholder for now)"""
    try:
        # This would trigger the universe filtering engine
        # For now, return a placeholder response
        return {
            "message": "Universe refresh triggered",
            "status": "in_progress",
            "estimated_completion": "10-15 minutes",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh universe: {str(e)}") 