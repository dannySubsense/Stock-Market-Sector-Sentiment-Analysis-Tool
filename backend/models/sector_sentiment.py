"""
Sector Sentiment Model - Tracks sentiment for 8 sectors with color classification
Used for the main sector grid dashboard
"""
from sqlalchemy import Column, String, Float, DateTime, Text, Integer
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from core.database import Base

class ColorClassification(str, Enum):
    """Color classification for sector sentiment"""
    DARK_RED = "dark_red"           # Strong bearish (-1.0 to -0.6)
    LIGHT_RED = "light_red"         # Moderate bearish (-0.6 to -0.2)
    BLUE_NEUTRAL = "blue_neutral"   # Neutral (-0.2 to +0.2)
    LIGHT_GREEN = "light_green"     # Moderate bullish (+0.2 to +0.6)
    DARK_GREEN = "dark_green"       # Strong bullish (+0.6 to +1.0)

class SectorSentiment(Base):
    """
    Sector Sentiment table - tracks sentiment for 8 sectors
    
    Sectors: technology, healthcare, energy, financial, consumer_discretionary,
             industrials, materials, utilities
    """
    __tablename__ = "sector_sentiment"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    sector = Column(String(50), nullable=False, index=True)
    
    # Sentiment scoring
    sentiment_score = Column(Float, nullable=False)  # -1.0 to +1.0
    color_classification = Column(String(20), nullable=False)  # ColorClassification enum
    confidence_level = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Multi-timeframe analysis
    timeframe_30min = Column(Float, nullable=True)  # 30-minute performance
    timeframe_1day = Column(Float, nullable=True)   # 1-day performance
    timeframe_3day = Column(Float, nullable=True)   # 3-day performance
    timeframe_1week = Column(Float, nullable=True)  # 1-week performance
    
    # Top stocks tracking
    top_bullish_stocks = Column(Text, nullable=True)  # JSON string of top 3 bullish
    top_bearish_stocks = Column(Text, nullable=True)  # JSON string of top 3 bearish
    
    # Analysis metadata
    last_updated = Column(DateTime, default=func.now())
    analysis_type = Column(String(20), default="background")  # background, on_demand
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SectorSentiment(sector='{self.sector}', score={self.sentiment_score}, color='{self.color_classification}')>"
    
    @classmethod
    def get_color_from_score(cls, score: float) -> ColorClassification:
        """Convert sentiment score to color classification"""
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
    
    @property
    def trading_signal(self) -> str:
        """Get trading signal from color classification"""
        signals = {
            ColorClassification.DARK_RED: "PRIME_SHORTING_ENVIRONMENT",
            ColorClassification.LIGHT_RED: "GOOD_SHORTING_ENVIRONMENT",
            ColorClassification.BLUE_NEUTRAL: "NEUTRAL_CAUTIOUS",
            ColorClassification.LIGHT_GREEN: "AVOID_SHORTS",
            ColorClassification.DARK_GREEN: "DO_NOT_SHORT"
        }
        return signals.get(ColorClassification(self.color_classification), "UNKNOWN")
    
    @property
    def sentiment_description(self) -> str:
        """Get human-readable sentiment description"""
        descriptions = {
            ColorClassification.DARK_RED: "Strong bearish sentiment, multiple negative catalysts",
            ColorClassification.LIGHT_RED: "Moderate bearish sentiment, some negative factors",
            ColorClassification.BLUE_NEUTRAL: "Mixed signals, sideways action expected",
            ColorClassification.LIGHT_GREEN: "Moderate bullish sentiment, upward momentum",
            ColorClassification.DARK_GREEN: "Strong bullish sentiment, squeeze risk high"
        }
        return descriptions.get(ColorClassification(self.color_classification), "Unknown sentiment")
    
    def update_sentiment(self, score: float, confidence: float = 0.8):
        """Update sentiment score and automatically set color"""
        self.sentiment_score = max(-1.0, min(1.0, score))  # Clamp between -1.0 and 1.0
        self.color_classification = self.get_color_from_score(self.sentiment_score).value
        self.confidence_level = max(0.0, min(1.0, confidence))  # Clamp between 0.0 and 1.0
        self.last_updated = datetime.utcnow()
    
    def get_timeframe_summary(self) -> Dict[str, Any]:
        """Get summary of all timeframes for frontend display"""
        return {
            "30min": {
                "value": self.timeframe_30min,
                "color": self.get_color_from_score(self.timeframe_30min or 0.0).value
            },
            "1day": {
                "value": self.timeframe_1day,
                "color": self.get_color_from_score(self.timeframe_1day or 0.0).value
            },
            "3day": {
                "value": self.timeframe_3day,
                "color": self.get_color_from_score(self.timeframe_3day or 0.0).value
            },
            "1week": {
                "value": self.timeframe_1week,
                "color": self.get_color_from_score(self.timeframe_1week or 0.0).value
            }
        }
    
    @property
    def is_stale(self) -> bool:
        """Check if sentiment data is stale (older than 1 hour)"""
        if not self.last_updated:
            return True
        return (datetime.utcnow() - self.last_updated).total_seconds() > 3600 