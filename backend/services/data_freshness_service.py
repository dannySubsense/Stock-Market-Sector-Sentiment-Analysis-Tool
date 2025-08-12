"""
Data Freshness Service - Batch-Based 1-Hour Staleness Detection
Returns complete sector batches with single staleness flag for UI gray card display
Works with atomic batch operations for reliable "all-or-nothing" sector data
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
import logging

from models.sector_sentiment_1d import SectorSentiment1D
from models.sector_sentiment_3d import SectorSentiment3D
from models.sector_sentiment_1w import SectorSentiment1W
from models.sector_sentiment_30min import SectorSentiment30M
from core.database import SessionLocal

logger = logging.getLogger(__name__)


class DataFreshnessService:
    """Service to validate data freshness using atomic batch operations"""

    def __init__(self):
        # Per-timeframe staleness thresholds
        self._staleness_thresholds: Dict[str, timedelta] = {
            "1day": timedelta(hours=1),
            "3day": timedelta(hours=24),
            "1week": timedelta(hours=72),
            "30min": timedelta(hours=1),
        }

    def get_latest_complete_batch(
        self, db: Session, timeframe: str = "1day"
    ) -> Tuple[List[Any], bool]:
        """
        Get the most recent complete batch of sector sentiment data

        Args:
            db: Database session
            timeframe: Timeframe to query (default: "1day")

        Returns:
            Tuple of (sector_records_list, is_stale_bool)
            Returns empty list if no complete batch found
        """
        try:
            # Select model by timeframe
            if timeframe == "1day":
                model = SectorSentiment1D
            elif timeframe == "3day":
                model = SectorSentiment3D
            elif timeframe in ("1week", "1w"):
                model = SectorSentiment1W
            elif timeframe in ("30min", "30m"):
                model = SectorSentiment30M
            else:
                model = SectorSentiment1D

            # Get the most recent batch_id for the selected timeframe
            latest_batch_result = (
                db.query(
                    model.batch_id,
                    func.max(model.timestamp).label("max_timestamp"),
                )
                .group_by(model.batch_id)
                .order_by(desc("max_timestamp"))
                .first()
            )

            if not latest_batch_result:
                logger.warning("No sector sentiment batches found")
                return [], True

            latest_batch_id = latest_batch_result.batch_id
            latest_timestamp = latest_batch_result.max_timestamp

            # Get all records from the latest batch for the timeframe
            batch_records = (
                db.query(model)
                .filter(model.batch_id == latest_batch_id)
                .order_by(model.sector)
                .all()
            )

            # Validate batch completeness (should have 11 sectors)
            if len(batch_records) != 11:
                logger.warning(
                    f"Incomplete batch {latest_batch_id}: "
                    f"{len(batch_records)} sectors instead of 11"
                )
                return [], True

            # Check if the entire batch is stale for this timeframe
            is_stale = self.is_batch_stale(latest_timestamp, timeframe=timeframe)

            logger.info(
                f"Retrieved complete batch {latest_batch_id} with "
                f"{len(batch_records)} sectors (stale: {is_stale})"
            )
            return batch_records, is_stale

        except Exception as e:
            logger.error(f"Error getting latest complete batch: {e}")
            return [], True

    def is_batch_stale(self, batch_timestamp: datetime, *, timeframe: str = "1day") -> bool:
        """
        Check if a batch is stale based on its timestamp

        Args:
            batch_timestamp: Timestamp of the batch to check

        Returns:
            True if batch is older than staleness threshold
        """
        # Normalize to UTC-aware datetimes for safe comparison
        threshold = self._staleness_thresholds.get(timeframe, timedelta(hours=1))
        cutoff_time = datetime.now(timezone.utc) - threshold
        ts = batch_timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts < cutoff_time

    def get_batch_age_info(self, batch_timestamp: datetime, *, timeframe: str = "1day") -> Dict[str, Any]:
        """
        Get detailed age information for a batch

        Args:
            batch_timestamp: Timestamp of the batch

        Returns:
            Dict with age details and staleness status
        """
        try:
            ts = batch_timestamp if batch_timestamp.tzinfo else batch_timestamp.replace(tzinfo=timezone.utc)
            age = datetime.now(timezone.utc) - ts
            is_stale = self.is_batch_stale(batch_timestamp, timeframe=timeframe)

            return {
                "is_stale": is_stale,
                "age_minutes": round(age.total_seconds() / 60, 1),
                "threshold_minutes": round(
                    self._staleness_thresholds.get(timeframe, timedelta(hours=1)).total_seconds() / 60
                ),
                "timestamp": ts.isoformat(),
                "status": "stale" if is_stale else "fresh",
            }

        except Exception as e:
            logger.error(f"Error getting batch age info: {e}")
            return {"is_stale": True, "error": str(e), "status": "unknown"}

    def get_all_batch_summaries(
        self, db: Session, timeframe: str = "1day", limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get summaries of recent batches for debugging/monitoring

        Args:
            db: Database session
            timeframe: Timeframe to get summaries for (30min, 1day, 3day, 1week)
            limit: Number of recent batches to return

        Returns:
            List of batch summary dictionaries for specified timeframe
        """
        try:
            if timeframe == "1day":
                model = SectorSentiment1D
            elif timeframe == "3day":
                model = SectorSentiment3D
            elif timeframe in ("1week", "1w"):
                model = SectorSentiment1W
            elif timeframe in ("30min", "30m"):
                model = SectorSentiment30M
            else:
                model = SectorSentiment1D
            # Get recent batches with their metadata for timeframe
            batch_summaries = (
                db.query(
                    model.batch_id,
                    func.count(model.sector).label("sector_count"),
                    func.min(model.timestamp).label("earliest"),
                    func.max(model.timestamp).label("latest"),
                    func.avg(model.sentiment_score).label("avg_sentiment"),
                )
                .group_by(model.batch_id)
                .order_by(desc("latest"))
                .limit(limit)
                .all()
            )

            summaries = []
            for batch in batch_summaries:
                age_info = self.get_batch_age_info(batch.latest, timeframe=timeframe)
                summaries.append(
                    {
                        "batch_id": batch.batch_id,
                        "sector_count": batch.sector_count,
                        "is_complete": batch.sector_count == 11,
                        "timestamp": batch.latest.isoformat(),
                        "timeframe": timeframe,  # Include timeframe in response
                        "age_minutes": age_info["age_minutes"],
                        "is_stale": age_info["is_stale"],
                        "avg_sentiment": round(
                            float(batch.avg_sentiment) if batch.avg_sentiment else 0.0, 3
                        ),
                    }
                )

            return summaries

        except Exception as e:
            logger.error(f"Error getting batch summaries for {timeframe}: {e}")
            return []

    def validate_batch_integrity(
        self, batch_records: List[Any]
    ) -> Dict[str, Any]:
        """
        Validate the integrity of a batch before serving to API

        Args:
            batch_records: List of SectorSentiment records from same batch

        Returns:
            Validation results with any issues found
        """
        if not batch_records:
            return {"valid": False, "issues": ["Empty batch"]}

        issues = []

        # Check sector count
        if len(batch_records) != 11:
            issues.append(f"Expected 11 sectors, got {len(batch_records)}")

        # Check batch ID consistency
        batch_ids = set(record.batch_id for record in batch_records)
        if len(batch_ids) != 1:
            issues.append(f"Multiple batch IDs in batch: {batch_ids}")

        # Check timestamp coherence (should be very close)
        timestamps = [record.timestamp for record in batch_records]
        if timestamps:
            time_spread = max(timestamps) - min(timestamps)
            if time_spread > timedelta(
                minutes=5
            ):  # Allow 5 minutes for analysis completion
                issues.append(f"Timestamps too spread out: {time_spread}")

        # Check for duplicate sectors
        sectors = [record.sector for record in batch_records]
        if len(set(sectors)) != len(sectors):
            issues.append("Duplicate sectors found in batch")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "batch_id": batch_records[0].batch_id if batch_records else None,
            "sector_count": len(batch_records),
            "timestamp_range": (
                f"{min(timestamps)} to {max(timestamps)}" if timestamps else None
            ),
        }

    def get_latest_batch_analysis_time(self, timeframe: str = "1day") -> Optional[datetime]:
        """Get timestamp of the most recent complete batch for specified timeframe"""
        try:
            with SessionLocal() as db:
                model = SectorSentiment1D if timeframe == "1day" else (
                    SectorSentiment3D if timeframe == "3day" else SectorSentiment1D
                )
                latest = db.query(func.max(model.timestamp)).scalar()
                return latest

        except Exception as e:
            logger.error(f"Error getting latest batch analysis time for {timeframe}: {e}")
            return None

    def clean_expired_batches(self, retention_days: int = 90) -> Dict[str, int]:
        """
        Clean complete batches older than retention period

        Args:
            retention_days: Days to retain batch data

        Returns:
            Dict with count of records cleaned
        """
        try:
            with SessionLocal() as db:
                cutoff_time = datetime.now(timezone.utc) - timedelta(
                    days=retention_days
                )

                # Get batch IDs to delete
                from models.sector_sentiment_1d import SectorSentiment1D
                old_batch_ids = (
                    db.query(SectorSentiment1D.batch_id)
                    .filter(SectorSentiment1D.timestamp < cutoff_time)
                    .distinct()
                    .all()
                )

                if not old_batch_ids:
                    return {"deleted_batches": 0, "deleted_records": 0}

                old_batch_list = [batch_id[0] for batch_id in old_batch_ids]

                # Delete all records from old batches
                deleted = (
                    db.query(SectorSentiment1D)
                    .filter(SectorSentiment1D.batch_id.in_(old_batch_list))
                    .delete(synchronize_session=False)
                )

                db.commit()

                logger.info(
                    f"Cleaned {len(old_batch_list)} batches ({deleted} records) "
                    f"older than {retention_days} days"
                )

                return {
                    "deleted_batches": len(old_batch_list),
                    "deleted_records": deleted,
                    "retention_days": retention_days,
                    "cutoff_time": cutoff_time.isoformat(),
                }

        except Exception as e:
            logger.error(f"Error cleaning expired batches: {e}")
            return {"error": str(e), "deleted_batches": 0, "deleted_records": 0}


# Global instance
_freshness_service: Optional[DataFreshnessService] = None


def get_freshness_service() -> DataFreshnessService:
    """Get global data freshness service instance"""
    global _freshness_service
    if _freshness_service is None:
        _freshness_service = DataFreshnessService()
    return _freshness_service
 