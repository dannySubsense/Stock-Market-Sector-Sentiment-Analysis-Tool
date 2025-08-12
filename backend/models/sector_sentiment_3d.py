"""
Sector Sentiment 3D Model
Timeframe-specific model for 3D sector sentiment analysis results
Mirrors the minimal 1D schema and serialization pattern.
"""

from sqlalchemy import Column, String, DateTime, Float, func
from enum import Enum
from typing import Dict, Any

from core.database import Base


class ColorClassification3D(Enum):
    """Enum for sector sentiment color classifications (same buckets as 1D)."""

    DARK_RED = "dark_red"
    LIGHT_RED = "light_red"
    BLUE_NEUTRAL = "blue_neutral"
    LIGHT_GREEN = "light_green"
    DARK_GREEN = "dark_green"


class SectorSentiment3D(Base):
    """
    3D Sector Sentiment Analysis Results
    Timeframe-specific table for 3D sentiment data with batch tracking
    """

    __tablename__ = "sector_sentiment_3d"

    # Primary key for 3D timeframe (same shape as 1D)
    sector = Column(String(100), nullable=False, primary_key=True)
    timestamp = Column(DateTime, nullable=False, primary_key=True)

    # Batch tracking for atomic operations
    batch_id = Column(String(50), nullable=False)

    # Core sentiment metrics
    sentiment_score = Column(Float, nullable=True)
    weighted_sentiment_score = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return (
            f"<SectorSentiment3D(sector='{self.sector}', "
            f"timestamp={self.timestamp}, score={self.sentiment_score})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses with derived fields."""
        score = self.sentiment_score if self.sentiment_score is not None else 0.0
        score_w = (
            self.weighted_sentiment_score
            if self.weighted_sentiment_score is not None
            else score
        )
        score_normalized = round(score / 100.0, 6)
        score_w_normalized = round(score_w / 100.0, 6)

        # Same bucket thresholds as 1D
        if score_normalized <= -0.01:
            color = ColorClassification3D.DARK_RED.value
        elif score_normalized <= -0.003:
            color = ColorClassification3D.LIGHT_RED.value
        elif score_normalized < 0.003:
            color = ColorClassification3D.BLUE_NEUTRAL.value
        elif score_normalized < 0.01:
            color = ColorClassification3D.LIGHT_GREEN.value
        else:
            color = ColorClassification3D.DARK_GREEN.value

        if score_normalized >= 0.01:
            trading_signal = "bullish"
        elif score_normalized <= -0.01:
            trading_signal = "bearish"
        else:
            trading_signal = "neutral"

        return {
            "sector": self.sector,
            "timeframe": "3d",
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "batch_id": self.batch_id,
            "sentiment_score": score,
            "weighted_sentiment_score": score_w,
            "sentiment_normalized": score_normalized,
            "sentiment_normalized_weighted": score_w_normalized,
            "color_classification": color,
            "trading_signal": trading_signal,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }



