"""
Sector Signal Metrics Model - Phase 2 Implementation (1D-Only)
Tracks sector sentiment signal quality and performance over time
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Index,
)

from core.database import Base


@dataclass
class SectorSignalMetrics:
    """Data structure for sector signal quality metrics (1D timeframe)"""

    sector: str
    timestamp: datetime

    # Core signal characteristics
    sentiment_score: float
    confidence_level: float
    sample_size: int

    # Statistical quality indicators
    outliers_removed: int
    significance_test_passed: bool
    sample_size_warning: bool

    # Volume and market context
    total_volume: int
    bullish_count: int
    bearish_count: int

    # Performance attribution (1D focus)
    volume_weighted_contribution: float
    statistical_confidence_factor: float
    data_quality_score: float

    # Historical context
    rolling_accuracy_7d: Optional[float] = None
    rolling_accuracy_30d: Optional[float] = None
    signal_consistency_score: Optional[float] = None


class SectorSignalMetricsDB(Base):
    """Database table for sector signal metrics tracking"""

    __tablename__ = "sector_signal_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sector = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)

    # Core signal characteristics
    sentiment_score = Column(Float, nullable=False)
    confidence_level = Column(Float, nullable=False)
    sample_size = Column(Integer, nullable=False)

    # Statistical quality indicators
    outliers_removed = Column(Integer, nullable=False, default=0)
    significance_test_passed = Column(Boolean, nullable=False, default=False)
    sample_size_warning = Column(Boolean, nullable=False, default=False)

    # Volume and market context
    total_volume = Column(Integer, nullable=False, default=0)
    bullish_count = Column(Integer, nullable=False, default=0)
    bearish_count = Column(Integer, nullable=False, default=0)

    # Performance attribution (1D focus)
    volume_weighted_contribution = Column(Float, nullable=False, default=0.0)
    statistical_confidence_factor = Column(Float, nullable=False, default=0.0)
    data_quality_score = Column(Float, nullable=False, default=0.0)

    # Historical context (optional)
    rolling_accuracy_7d = Column(Float, nullable=True)
    rolling_accuracy_30d = Column(Float, nullable=True)
    signal_consistency_score = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index("idx_sector_timestamp", "sector", "timestamp"),
        Index("idx_timestamp_desc", "timestamp"),
        Index("idx_sector_confidence", "sector", "confidence_level"),
    )

    def __repr__(self):
        return (
            f"<SectorSignalMetrics("
            f"sector='{self.sector}', "
            f"sentiment={self.sentiment_score:.3f}, "
            f"confidence={self.confidence_level:.3f}, "
            f"timestamp='{self.timestamp}'"
            f")>"
        )
