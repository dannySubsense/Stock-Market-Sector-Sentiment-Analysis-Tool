"""
Stock Data Model - Tracks individual stock performance and price movements
Used for sector sentiment calculations and ranking
"""
from sqlalchemy import Column, String, Float, DateTime, BigInteger, Boolean, Text, Integer
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

from core.database import Base

class StockData(Base):
    """
    Stock Data table - tracks real-time and historical stock performance
    Used for sector sentiment calculations and top stock rankings
    """
    __tablename__ = "stock_data"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    
    # Basic price data
    current_price = Column(Float, nullable=False)
    previous_close = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    
    # Volume data
    volume = Column(BigInteger, nullable=False)
    avg_volume_20d = Column(BigInteger, nullable=True)  # 20-day average volume
    volume_ratio = Column(Float, nullable=True)  # current_volume / avg_volume
    
    # Performance metrics
    price_change = Column(Float, nullable=False)  # Absolute price change
    price_change_percent = Column(Float, nullable=False)  # Percentage change
    
    # Gap analysis
    gap_size = Column(Float, nullable=True)  # Gap from previous close
    gap_percent = Column(Float, nullable=True)  # Gap percentage
    is_gap_up = Column(Boolean, nullable=True)  # True if gap up, False if gap down
    
    # Multi-timeframe performance
    performance_30min = Column(Float, nullable=True)  # 30-minute performance
    performance_1day = Column(Float, nullable=True)   # 1-day performance
    performance_3day = Column(Float, nullable=True)   # 3-day performance
    performance_1week = Column(Float, nullable=True)  # 1-week performance
    
    # Sector context
    sector = Column(String(50), nullable=False, index=True)
    sector_relative_performance = Column(Float, nullable=True)  # Performance vs sector
    
    # Ranking data
    bullish_rank = Column(Integer, nullable=True)  # Rank in bullish list (1-3)
    bearish_rank = Column(Integer, nullable=True)  # Rank in bearish list (1-3)
    ranking_score = Column(Float, nullable=True)  # Composite ranking score
    
    # Analysis metadata
    last_updated = Column(DateTime, default=func.now())
    data_source = Column(String(20), default="polygon")  # polygon, fmp, etc.
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<StockData(symbol='{self.symbol}', price={self.current_price}, change={self.price_change_percent:.2f}%)>"
    
    @property
    def is_gap_trade(self) -> bool:
        """Check if stock has significant gap (>5%)"""
        return self.gap_percent is not None and abs(self.gap_percent) >= 0.05
    
    @property
    def is_large_gap(self) -> bool:
        """Check if stock has large gap (>15%)"""
        return self.gap_percent is not None and abs(self.gap_percent) >= 0.15
    
    @property
    def is_extreme_gap(self) -> bool:
        """Check if stock has extreme gap (>30%)"""
        return self.gap_percent is not None and abs(self.gap_percent) >= 0.30
    
    @property
    def has_volume_confirmation(self) -> bool:
        """Check if move has volume confirmation (>1.5x average)"""
        return self.volume_ratio is not None and self.volume_ratio >= 1.5
    
    @property
    def is_bullish_candidate(self) -> bool:
        """Check if stock is a good bullish candidate"""
        return (
            self.price_change_percent > 0 and
            self.has_volume_confirmation and
            not self.is_extreme_gap  # Avoid exhausted moves
        )
    
    @property
    def is_bearish_candidate(self) -> bool:
        """Check if stock is a good bearish candidate"""
        return (
            self.price_change_percent < 0 and
            self.has_volume_confirmation
        )
    
    def calculate_ranking_score(self, sector_sentiment: float) -> float:
        """
        Calculate composite ranking score based on multiple factors
        
        Args:
            sector_sentiment: Current sector sentiment (-1.0 to 1.0)
            
        Returns:
            Ranking score (0-10)
        """
        score = 0.0
        
        # Gap magnitude (40% weight)
        gap_score = min(abs(self.gap_percent or 0) * 10, 4.0)
        score += gap_score
        
        # Volume confirmation (30% weight)
        volume_score = min((self.volume_ratio or 1.0) * 1.5, 3.0)
        score += volume_score
        
        # Sector alignment (20% weight)
        if sector_sentiment > 0.2 and self.price_change_percent > 0:
            # Bullish sector, bullish stock
            score += 2.0
        elif sector_sentiment < -0.2 and self.price_change_percent < 0:
            # Bearish sector, bearish stock
            score += 2.0
        elif abs(sector_sentiment) <= 0.2:
            # Neutral sector
            score += 1.0
        
        # Shortability preview (10% weight) - placeholder
        # This would be enhanced with actual float data
        if abs(self.price_change_percent) > 0.1:  # Significant move
            score += 1.0
        
        return min(score, 10.0)  # Cap at 10
    
    def update_performance_data(self, 
                              current_price: float,
                              volume: int,
                              previous_close: float,
                              open_price: float,
                              high: float,
                              low: float):
        """Update stock performance data"""
        self.current_price = current_price
        self.volume = volume
        self.previous_close = previous_close
        self.open_price = open_price
        self.high_price = high
        self.low_price = low
        
        # Calculate derived metrics
        self.price_change = current_price - previous_close
        self.price_change_percent = (current_price - previous_close) / previous_close if previous_close > 0 else 0
        
        # Calculate gap
        self.gap_size = open_price - previous_close
        self.gap_percent = (open_price - previous_close) / previous_close if previous_close > 0 else 0
        self.is_gap_up = self.gap_size > 0
        
        # Calculate volume ratio
        if self.avg_volume_20d and self.avg_volume_20d > 0:
            self.volume_ratio = volume / self.avg_volume_20d
        
        self.last_updated = datetime.utcnow()
    
    def get_display_data(self) -> Dict[str, Any]:
        """Get data formatted for frontend display"""
        return {
            "symbol": self.symbol,
            "current_price": self.current_price,
            "price_change": self.price_change,
            "price_change_percent": self.price_change_percent,
            "volume": self.volume,
            "volume_ratio": self.volume_ratio,
            "gap_percent": self.gap_percent,
            "sector": self.sector,
            "is_gap_trade": self.is_gap_trade,
            "is_large_gap": self.is_large_gap,
            "is_extreme_gap": self.is_extreme_gap,
            "has_volume_confirmation": self.has_volume_confirmation,
            "last_updated": self.last_updated
        } 