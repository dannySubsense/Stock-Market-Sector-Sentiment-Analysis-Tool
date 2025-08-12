"""
Sector Sentiment 30min Model (intraday)
"""

from sqlalchemy import Column, String, DateTime, Float, func
from typing import Dict, Any
from enum import Enum

from core.database import Base


class ColorClassification30M(Enum):
    DARK_RED = "dark_red"
    LIGHT_RED = "light_red"
    BLUE_NEUTRAL = "blue_neutral"
    LIGHT_GREEN = "light_green"
    DARK_GREEN = "dark_green"


class SectorSentiment30M(Base):
    __tablename__ = "sector_sentiment_30min"

    sector = Column(String(100), primary_key=True, nullable=False)
    timestamp = Column(DateTime, primary_key=True, nullable=False)
    batch_id = Column(String(50), nullable=False)
    sentiment_score = Column(Float, nullable=True)
    weighted_sentiment_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        score = float(self.sentiment_score or 0.0)
        score_w = float(self.weighted_sentiment_score if self.weighted_sentiment_score is not None else score)
        n = round(score / 100.0, 6)
        nw = round(score_w / 100.0, 6)

        if n <= -0.01:
            color = ColorClassification30M.DARK_RED.value
        elif n <= -0.003:
            color = ColorClassification30M.LIGHT_RED.value
        elif n < 0.003:
            color = ColorClassification30M.BLUE_NEUTRAL.value
        elif n < 0.01:
            color = ColorClassification30M.LIGHT_GREEN.value
        else:
            color = ColorClassification30M.DARK_GREEN.value

        if n >= 0.01:
            signal = "bullish"
        elif n <= -0.01:
            signal = "bearish"
        else:
            signal = "neutral"

        return {
            "sector": self.sector,
            "timeframe": "30min",
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "batch_id": self.batch_id,
            "sentiment_score": score,
            "weighted_sentiment_score": score_w,
            "sentiment_normalized": n,
            "sentiment_normalized_weighted": nw,
            "color_classification": color,
            "trading_signal": signal,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


