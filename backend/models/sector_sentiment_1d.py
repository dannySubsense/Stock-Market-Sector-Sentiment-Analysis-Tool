"""
Sector Sentiment 1D Models for Market Analysis
Timeframe-specific model for 1D sector sentiment analysis results
Part of segregated timeframe architecture (1d, 3d, 1w, 30m tables)
"""

from sqlalchemy import Column, String, DateTime, Float, Integer, func, JSON
from enum import Enum
from typing import Dict, Any

from core.database import Base


class ColorClassification(Enum):
    """Enum for sector sentiment color classifications"""

    DARK_RED = "dark_red"  # Strong bearish (-1.0 to -0.6)
    LIGHT_RED = "light_red"  # Moderate bearish (-0.6 to -0.2)
    BLUE_NEUTRAL = "blue_neutral"  # Neutral (-0.2 to +0.2)
    LIGHT_GREEN = "light_green"  # Moderate bullish (+0.2 to +0.6)
    DARK_GREEN = "dark_green"  # Strong bullish (+0.6 to +1.0)


class SectorSentiment1D(Base):
    """
    1D Sector Sentiment Analysis Results
    Timeframe-specific table for 1D sentiment data with batch tracking
    Part of segregated architecture: sector_sentiment_1d, sector_sentiment_3d, etc.
    """

    __tablename__ = "sector_sentiment_1d"

    # Primary key for 1D timeframe (simplified from multi-timeframe)
    sector = Column(String(100), nullable=False, primary_key=True)
    timestamp = Column(DateTime, nullable=False, primary_key=True)

    # Batch tracking for atomic operations
    batch_id = Column(String(50), nullable=False)

    # Core sentiment metrics
    sentiment_score = Column(Float, nullable=True)

    # Note: Gapper rankings moved to separate sector_gappers_1d table

    # Metadata
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return (
            f"<SectorSentiment1D(sector='{self.sector}', "
            f"timestamp={self.timestamp}, score={self.sentiment_score})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses with derived fields."""
        score = self.sentiment_score if self.sentiment_score is not None else 0.0
        score_normalized = round(score / 100.0, 6)

        # Derive color classification from score with tighter 1D small-cap buckets
        # normalized = percent/100.0
        if score_normalized <= -0.01:  # ≤ -1.0%
            color = ColorClassification.DARK_RED.value
        elif score_normalized <= -0.003:  # -1.0% .. -0.3%
            color = ColorClassification.LIGHT_RED.value
        elif score_normalized < 0.003:  # -0.3% .. +0.3%
            color = ColorClassification.BLUE_NEUTRAL.value
        elif score_normalized < 0.01:  # +0.3% .. +1.0%
            color = ColorClassification.LIGHT_GREEN.value
        else:
            color = ColorClassification.DARK_GREEN.value

        # Simple trading signal derived from score (no DB change)
        if score_normalized >= 0.01:
            trading_signal = "bullish"
        elif score_normalized <= -0.01:
            trading_signal = "bearish"
        else:
            trading_signal = "neutral"

        return {
            "sector": self.sector,
            "timeframe": "1d",
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "batch_id": self.batch_id,
            "sentiment_score": score,
            "sentiment_normalized": score_normalized,
            "color_classification": color,
            "trading_signal": trading_signal,
            # Note: Gapper data available in separate sector_gappers_1d table
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
