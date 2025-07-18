"""
Stock Universe Model - Tracks the 1,500 small-cap stocks
Market Cap Focus: $10M - $2B (micro-cap to small-cap)
"""
from sqlalchemy import Column, String, BigInteger, Float, DateTime, Boolean, Integer
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from core.database import Base

class StockUniverse(Base):
    """
    Stock Universe table - tracks small-cap stocks that meet our criteria
    
    Selection Criteria:
    - Market Cap: $10M - $2B
    - Min Daily Volume: 1M+ shares
    - Min Price: $2.00
    - Exchange: NASDAQ/NYSE
    """
    __tablename__ = "stock_universe"
    
    # Primary key
    symbol = Column(String(10), primary_key=True, index=True)
    
    # Company information
    company_name = Column(String(200), nullable=False)
    exchange = Column(String(20), nullable=False)  # NASDAQ, NYSE, etc.
    
    # Market data for filtering
    market_cap = Column(BigInteger, nullable=False)  # Market cap in USD
    avg_daily_volume = Column(BigInteger, nullable=False)  # 20-day average volume
    current_price = Column(Float, nullable=False)
    
    # Sector classification
    sector = Column(String(50), nullable=False)  # One of 8 sectors
    volatility_multiplier = Column(Float, default=1.0)  # Sector-specific multiplier
    
    # Gap analysis
    gap_frequency = Column(String(20), default="medium")  # low, medium, high, extreme
    
    # Shortability assessment
    float_shares = Column(BigInteger, nullable=True)  # Shares available for shorting
    shortability_score = Column(Float, nullable=True)  # 0-10 scale
    
    # Status tracking
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=func.now())
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<StockUniverse(symbol='{self.symbol}', sector='{self.sector}', market_cap={self.market_cap})>"
    
    @property
    def market_cap_formatted(self) -> str:
        """Format market cap for display"""
        if self.market_cap >= 1_000_000_000:
            return f"${self.market_cap / 1_000_000_000:.1f}B"
        elif self.market_cap >= 1_000_000:
            return f"${self.market_cap / 1_000_000:.0f}M"
        else:
            return f"${self.market_cap:,.0f}"
    
    @property
    def is_micro_cap(self) -> bool:
        """Check if stock is micro-cap (<$300M)"""
        return self.market_cap < 300_000_000
    
    @property
    def is_small_cap(self) -> bool:
        """Check if stock is small-cap ($300M - $2B)"""
        return 300_000_000 <= self.market_cap <= 2_000_000_000
    
    @property
    def meets_volume_criteria(self) -> bool:
        """Check if stock meets minimum volume criteria"""
        return self.avg_daily_volume >= 1_000_000
    
    @property
    def meets_price_criteria(self) -> bool:
        """Check if stock meets price criteria"""
        return 2.00 <= self.current_price <= 100.00
    
    def should_include_in_universe(self) -> bool:
        """Check if stock should be included in the universe"""
        return (
            self.is_active and
            (self.is_micro_cap or self.is_small_cap) and
            self.meets_volume_criteria and
            self.meets_price_criteria and
            self.exchange in ["NASDAQ", "NYSE", "NYSEARCA"]
        ) 