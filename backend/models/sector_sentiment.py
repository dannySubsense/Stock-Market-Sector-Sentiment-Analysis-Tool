"""
Sector Sentiment Models for Market Analysis
Represents sector-level sentiment analysis results with atomic batch tracking
"""

from sqlalchemy import Column, String, DateTime, Float, Integer, BigInteger, func
from enum import Enum
from datetime import datetime
from typing import Dict, Any

from core.database import Base


class ColorClassification(Enum):
    """Enum for sector sentiment color classifications"""

    DARK_RED = "dark_red"  # Strong bearish (-1.0 to -0.6)
    LIGHT_RED = "light_red"  # Moderate bearish (-0.6 to -0.2)
    BLUE_NEUTRAL = "blue_neutral"  # Neutral (-0.2 to +0.2)
    LIGHT_GREEN = "light_green"  # Moderate bullish (+0.2 to +0.6)
    DARK_GREEN = "dark_green"  # Strong bullish (+0.6 to +1.0)


class SectorSentiment(Base):
    """
    Sector Sentiment Analysis Results with Batch Tracking

    Stores timestamped sector sentiment calculations with atomic batch IDs
    for reliable "all-or-nothing" sector analysis retrieval
    """

    __tablename__ = "sector_sentiment"

    # Composite primary key for multi-timeframe support
    sector = Column(String(100), nullable=False, primary_key=True)
    timeframe = Column(String(10), nullable=False, primary_key=True)
    timestamp = Column(DateTime, nullable=False, primary_key=True)

    # Batch tracking for atomic operations
    batch_id = Column(String(50), nullable=False)

    # Core sentiment metrics
    sentiment_score = Column(Float, nullable=True)
    bullish_count = Column(Integer, nullable=True)
    bearish_count = Column(Integer, nullable=True)
    total_volume = Column(BigInteger, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=func.now())

    def get_color_from_score(self, score: float) -> ColorClassification:
        """
        Convert sentiment score to color classification

        Args:
            score: Sentiment score between -1.0 and +1.0

        Returns:
            ColorClassification enum value
        """
        if score <= -0.6:
            return ColorClassification.DARK_RED
        elif score <= -0.2:
            return ColorClassification.LIGHT_RED
        elif score <= 0.2:
            return ColorClassification.BLUE_NEUTRAL
        elif score <= 0.6:
            return ColorClassification.LIGHT_GREEN
        else:
            return ColorClassification.DARK_GREEN

    def get_trading_signal_from_color(self, color: ColorClassification) -> str:
        """Get trading signal from color classification"""
        signal_mapping = {
            ColorClassification.DARK_RED: "PRIME_SHORTING_ENVIRONMENT",
            ColorClassification.LIGHT_RED: "GOOD_SHORTING_ENVIRONMENT",
            ColorClassification.BLUE_NEUTRAL: "NEUTRAL_CAUTIOUS",
            ColorClassification.LIGHT_GREEN: "AVOID_SHORTS",
            ColorClassification.DARK_GREEN: "DO_NOT_SHORT",
        }
        return signal_mapping.get(color, "NEUTRAL_CAUTIOUS")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        color = self.get_color_from_score(self.sentiment_score or 0.0)

        return {
            "sector": self.sector,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "batch_id": self.batch_id,
            "sentiment_score": (
                float(self.sentiment_score) if self.sentiment_score else 0.0
            ),
            "color_classification": color.value,
            "trading_signal": self.get_trading_signal_from_color(color),
            "bullish_count": self.bullish_count or 0,
            "bearish_count": self.bearish_count or 0,
            "total_volume": self.total_volume or 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def is_stale(self, hours_threshold: int = 1) -> bool:
        """
        Check if this record is considered stale

        Args:
            hours_threshold: Hours after which data is considered stale

        Returns:
            True if data is older than threshold
        """
        if not self.timestamp:
            return True

        from datetime import timezone, timedelta

        age = datetime.now(timezone.utc) - self.timestamp
        return age > timedelta(hours=hours_threshold)

    def __repr__(self):
        return (
            f"<SectorSentiment(sector={self.sector}, "
            f"timeframe={self.timeframe}, "
            f"batch_id={self.batch_id}, "
            f"sentiment_score={self.sentiment_score})>"
        )
