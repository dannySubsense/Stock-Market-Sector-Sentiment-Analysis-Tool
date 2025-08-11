"""
Sector Gappers 1D Models for Market Analysis
Timeframe-specific model for 1D sector gapper rankings
Separate from sector sentiment for cleaner architecture
"""

from sqlalchemy import Column, String, DateTime, Float, Integer, func, Enum
from enum import Enum as PyEnum
from typing import Dict, Any

from core.database import Base


class GapperType(PyEnum):
    """Enum for gapper types"""
    GAINER = "gainer"
    LOSER = "loser"


class SectorGappers1D(Base):
    """
    1D Sector Gapper Rankings
    Timeframe-specific table for 1D gapper data with batch tracking
    Separate from sector sentiment for cleaner architecture
    """

    __tablename__ = "sector_gappers_1d"

    # Primary key for 1D timeframe
    sector = Column(String(100), nullable=False, primary_key=True)
    timestamp = Column(DateTime, nullable=False, primary_key=True)
    gapper_type = Column(Enum(GapperType), nullable=False, primary_key=True)
    rank = Column(Integer, nullable=False, primary_key=True)

    # Batch tracking for atomic operations
    batch_id = Column(String(50), nullable=False)

    # Gapper data
    symbol = Column(String(20), nullable=False)
    changes_percentage = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    current_price = Column(Float, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return (
            f"<SectorGappers1D(sector='{self.sector}', "
            f"type={self.gapper_type}, rank={self.rank}, "
            f"symbol={self.symbol})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "sector": self.sector,
            "timeframe": "1d",  # Always 1d for this model
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "batch_id": self.batch_id,
            "gapper_type": self.gapper_type.value,
            "rank": self.rank,
            "symbol": self.symbol,
            "changes_percentage": self.changes_percentage,
            "volume": self.volume,
            "current_price": self.current_price,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        } 