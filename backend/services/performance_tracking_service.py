"""
Performance Tracking Service - Phase 2 Implementation (1D-Only)
Monitors sector signal quality and tracks performance over time
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.database import SessionLocal
from models.sector_signal_metrics import SectorSignalMetrics, SectorSignalMetricsDB

logger = logging.getLogger(__name__)


class PerformanceTrackingService:
    """Service for tracking sector signal performance and quality metrics"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        """Get database session, create new one if not provided"""
        return self.db_session or SessionLocal()

    def record_signal_metrics(self, signal_metrics: SectorSignalMetrics) -> bool:
        """
        Record sector signal metrics with historical context
        """
        session = self._get_session()

        try:
            # Calculate historical context before storing
            enhanced_metrics = self._enhance_with_historical_context(
                signal_metrics, session
            )

            # Create database record
            db_record = SectorSignalMetricsDB(
                sector=enhanced_metrics.sector,
                timestamp=enhanced_metrics.timestamp,
                sentiment_score=enhanced_metrics.sentiment_score,
                confidence_level=enhanced_metrics.confidence_level,
                sample_size=enhanced_metrics.sample_size,
                outliers_removed=enhanced_metrics.outliers_removed,
                significance_test_passed=enhanced_metrics.significance_test_passed,
                sample_size_warning=enhanced_metrics.sample_size_warning,
                total_volume=enhanced_metrics.total_volume,
                bullish_count=enhanced_metrics.bullish_count,
                bearish_count=enhanced_metrics.bearish_count,
                volume_weighted_contribution=enhanced_metrics.volume_weighted_contribution,
                statistical_confidence_factor=enhanced_metrics.statistical_confidence_factor,
                data_quality_score=enhanced_metrics.data_quality_score,
                rolling_accuracy_7d=enhanced_metrics.rolling_accuracy_7d,
                rolling_accuracy_30d=enhanced_metrics.rolling_accuracy_30d,
                signal_consistency_score=enhanced_metrics.signal_consistency_score,
            )

            session.add(db_record)
            session.commit()

            logger.info(
                f"Recorded signal metrics for {enhanced_metrics.sector}: "
                f"sentiment={enhanced_metrics.sentiment_score:.3f}, "
                f"confidence={enhanced_metrics.confidence_level:.3f}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to record signal metrics: {e}")
            session.rollback()
            return False

        finally:
            if not self.db_session:
                session.close()

    def _enhance_with_historical_context(
        self, signal_metrics: SectorSignalMetrics, session: Session
    ) -> SectorSignalMetrics:
        """
        Enhance signal metrics with historical performance context
        """
        try:
            # Calculate rolling accuracy (7-day)
            rolling_7d = self._calculate_rolling_accuracy(
                signal_metrics.sector, 7, session
            )

            # Calculate rolling accuracy (30-day)
            rolling_30d = self._calculate_rolling_accuracy(
                signal_metrics.sector, 30, session
            )

            # Calculate signal consistency score
            consistency_score = self._calculate_signal_consistency(
                signal_metrics.sector, session
            )

            # Update the signal metrics with historical context
            signal_metrics.rolling_accuracy_7d = rolling_7d
            signal_metrics.rolling_accuracy_30d = rolling_30d
            signal_metrics.signal_consistency_score = consistency_score

            return signal_metrics

        except Exception as e:
            logger.warning(f"Failed to enhance with historical context: {e}")
            return signal_metrics

    def _calculate_rolling_accuracy(
        self, sector: str, days: int, session: Session
    ) -> Optional[float]:
        """
        Calculate rolling accuracy over specified number of days
        Note: This is a placeholder - actual accuracy calculation would require
        comparing predicted vs actual performance
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get recent signal metrics for this sector
            recent_metrics = (
                session.query(SectorSignalMetricsDB)
                .filter(
                    SectorSignalMetricsDB.sector == sector,
                    SectorSignalMetricsDB.timestamp >= cutoff_date,
                )
                .order_by(desc(SectorSignalMetricsDB.timestamp))
                .limit(50)  # Reasonable sample size
                .all()
            )

            if len(recent_metrics) < 3:
                return None

            # Placeholder accuracy calculation
            # In production, this would compare predictions vs actual outcomes
            avg_confidence = sum(m.confidence_level for m in recent_metrics) / len(
                recent_metrics
            )

            # Simple heuristic: higher average confidence suggests better accuracy
            # This should be replaced with actual prediction vs outcome comparison
            rolling_accuracy = min(1.0, avg_confidence * 1.1)

            return rolling_accuracy

        except Exception as e:
            logger.warning(f"Failed to calculate rolling accuracy: {e}")
            return None

    def _calculate_signal_consistency(
        self, sector: str, session: Session
    ) -> Optional[float]:
        """
        Calculate signal consistency score based on recent sentiment variance
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=14)

            # Get recent sentiment scores
            recent_scores = (
                session.query(SectorSignalMetricsDB.sentiment_score)
                .filter(
                    SectorSignalMetricsDB.sector == sector,
                    SectorSignalMetricsDB.timestamp >= cutoff_date,
                )
                .order_by(desc(SectorSignalMetricsDB.timestamp))
                .limit(20)
                .all()
            )

            if len(recent_scores) < 3:
                return None

            scores = [score[0] for score in recent_scores]

            # Calculate consistency as inverse of variance
            # More consistent signals have lower variance
            mean_score = sum(scores) / len(scores)
            variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)

            # Convert to consistency score (0-1, higher is more consistent)
            consistency_score = max(0.0, 1.0 - (variance * 2.0))

            return consistency_score

        except Exception as e:
            logger.warning(f"Failed to calculate signal consistency: {e}")
            return None

    def get_sector_performance_summary(
        self, sector: str, days: int = 30
    ) -> Optional[Dict]:
        """
        Get performance summary for a sector over specified days
        """
        session = self._get_session()

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            metrics = (
                session.query(SectorSignalMetricsDB)
                .filter(
                    SectorSignalMetricsDB.sector == sector,
                    SectorSignalMetricsDB.timestamp >= cutoff_date,
                )
                .order_by(desc(SectorSignalMetricsDB.timestamp))
                .all()
            )

            if not metrics:
                return None

            # Calculate summary statistics
            latest_metric = metrics[0]
            avg_sentiment = sum(m.sentiment_score for m in metrics) / len(metrics)
            avg_confidence = sum(m.confidence_level for m in metrics) / len(metrics)
            avg_sample_size = sum(m.sample_size for m in metrics) / len(metrics)

            return {
                "sector": sector,
                "period_days": days,
                "total_signals": len(metrics),
                "latest_sentiment": latest_metric.sentiment_score,
                "latest_confidence": latest_metric.confidence_level,
                "avg_sentiment": avg_sentiment,
                "avg_confidence": avg_confidence,
                "avg_sample_size": int(avg_sample_size),
                "rolling_accuracy_7d": latest_metric.rolling_accuracy_7d,
                "rolling_accuracy_30d": latest_metric.rolling_accuracy_30d,
                "signal_consistency": latest_metric.signal_consistency_score,
                "last_updated": latest_metric.timestamp.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return None

        finally:
            if not self.db_session:
                session.close()

    def get_all_sectors_performance(self, days: int = 30) -> Dict[str, Dict]:
        """
        Get performance summaries for all sectors
        """
        session = self._get_session()

        try:
            # Get all sectors with recent data
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            sectors = (
                session.query(SectorSignalMetricsDB.sector)
                .filter(SectorSignalMetricsDB.timestamp >= cutoff_date)
                .distinct()
                .all()
            )

            performance_data = {}

            for sector_tuple in sectors:
                sector = sector_tuple[0]
                summary = self.get_sector_performance_summary(sector, days)
                if summary:
                    performance_data[sector] = summary

            return performance_data

        except Exception as e:
            logger.error(f"Failed to get all sectors performance: {e}")
            return {}

        finally:
            if not self.db_session:
                session.close()


def get_performance_tracking_service() -> PerformanceTrackingService:
    """Factory function to get PerformanceTrackingService instance"""
    return PerformanceTrackingService()
