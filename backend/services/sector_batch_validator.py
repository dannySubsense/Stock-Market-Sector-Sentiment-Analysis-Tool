"""
Sector Batch Validator - Ensures Atomic "All-or-Nothing" Sector Analysis
Validates complete 11-sector batches before database storage
Generates unique batch IDs for reliable data retrieval
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import logging

from models.sector_sentiment_1d import SectorSentiment1D

logger = logging.getLogger(__name__)


class SectorBatchValidationError(Exception):
    """Raised when sector batch validation fails"""

    pass


class SectorBatchValidator:
    """
    Validates and prepares sector analysis results for atomic batch storage
    Ensures exactly 11 sectors are present before allowing database operations
    """

    def __init__(self):
        # Expected sectors from SDD (11 FMP sectors)
        self.expected_sectors = {
            "basic_materials",
            "communication_services",
            "consumer_cyclical",
            "consumer_defensive",
            "energy",
            "financial_services",
            "healthcare",
            "industrials",
            "real_estate",
            "technology",
            "utilities",
        }

    def generate_batch_id(self) -> str:
        """
        Generate unique batch ID for analysis run

        Returns:
            Unique batch identifier (timestamp + UUID)
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"batch_{timestamp}_{short_uuid}"

    def validate_sector_completeness(
        self, sector_results: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all expected sectors are present

        Args:
            sector_results: Dictionary of sector analysis results

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check sector count
        if len(sector_results) != 11:
            issues.append(f"Expected 11 sectors, got {len(sector_results)}")

        # Check for missing sectors
        provided_sectors = set(sector_results.keys())
        missing_sectors = self.expected_sectors - provided_sectors
        if missing_sectors:
            issues.append(f"Missing sectors: {sorted(missing_sectors)}")

        # Check for unexpected sectors
        unexpected_sectors = provided_sectors - self.expected_sectors
        if unexpected_sectors:
            issues.append(f"Unexpected sectors: {sorted(unexpected_sectors)}")

        # Check for duplicate sectors (shouldn't happen with dict, but safety check)
        if len(provided_sectors) != len(sector_results):
            issues.append("Duplicate sectors detected in results")

        return len(issues) == 0, issues

    def validate_sector_data_quality(
        self, sector_results: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate the quality of sector data

        Args:
            sector_results: Dictionary of sector analysis results

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        for sector_name, sector_data in sector_results.items():
            # Check required fields
            if not isinstance(sector_data, dict):
                issues.append(f"{sector_name}: Data is not a dictionary")
                continue

            # Check sentiment score
            sentiment_score = sector_data.get("sentiment_score")
            if sentiment_score is None:
                issues.append(f"{sector_name}: Missing sentiment_score")
            elif not isinstance(sentiment_score, (int, float)):
                issues.append(f"{sector_name}: sentiment_score must be numeric")
            # Validated pipeline uses simple average of changes_percentage (percent units)
            elif not (-100.0 <= sentiment_score <= 100.0):
                issues.append(
                    f"{sector_name}: sentiment_score must be between -100.0 and 100.0 (percent units), "
                    f"got {sentiment_score}"
                )

            # Check bullish/bearish lists
            for list_type in ["top_bullish", "top_bearish"]:
                stock_list = sector_data.get(list_type, [])
                if not isinstance(stock_list, list):
                    issues.append(f"{sector_name}: {list_type} must be a list")
                elif len(stock_list) > 10:  # Reasonable upper bound
                    issues.append(
                        f"{sector_name}: {list_type} has too many stocks ({len(stock_list)})"
                    )

            # Check volume
            total_volume = sector_data.get("total_volume", 0)
            if not isinstance(total_volume, (int, float)) or total_volume < 0:
                issues.append(
                    f"{sector_name}: total_volume must be non-negative number"
                )

        return len(issues) == 0, issues

    def prepare_batch(
        self,
        sector_results: Dict[str, Any],
        timeframe: str = "1day",
        analysis_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[SectorSentiment1D]:
        """
        Prepare validated sector batch for storage

        Args:
            sector_results: Raw sector analysis results
            timeframe: Analysis timeframe (default: "1day")
            analysis_metadata: Optional metadata about the analysis

        Returns:
            List of validated SectorSentiment records ready for storage

        Raises:
            SectorBatchValidationError: If validation fails
        """
        logger.info("Starting sector batch validation")

        # Validate completeness
        is_complete, completeness_issues = self.validate_sector_completeness(
            sector_results
        )
        if not is_complete:
            error_msg = f"Sector completeness validation failed: {'; '.join(completeness_issues)}"
            logger.error(error_msg)
            raise SectorBatchValidationError(error_msg)

        # Validate data quality
        is_quality, quality_issues = self.validate_sector_data_quality(sector_results)
        if not is_quality:
            error_msg = (
                f"Sector data quality validation failed: {'; '.join(quality_issues)}"
            )
            logger.error(error_msg)
            raise SectorBatchValidationError(error_msg)

        # Generate batch ID for this analysis run
        batch_id = self.generate_batch_id()
        current_time = datetime.now(timezone.utc)

        logger.info(
            f"Creating validated batch {batch_id} with {len(sector_results)} sectors"
        )

        # Create SectorSentiment1D records (minimal 1D schema per validated pipeline)
        batch_records = []
        for sector_name, sector_data in sector_results.items():
            record = SectorSentiment1D(
                sector=sector_name,
                timestamp=current_time,
                batch_id=batch_id,
                sentiment_score=sector_data.get("sentiment_score", 0.0),
                created_at=current_time,
            )
            batch_records.append(record)

        logger.info(f"✅ Batch validation successful: {batch_id}")
        return batch_records

    def get_batch_summary(self, batch_records: List[SectorSentiment1D]) -> Dict[str, Any]:
        """
        Get summary information about a validated batch

        Args:
            batch_records: List of validated SectorSentiment records

        Returns:
            Batch summary information
        """
        if not batch_records:
            return {"error": "Empty batch"}

        batch_id = batch_records[0].batch_id
        sectors = [record.sector for record in batch_records]
        sentiment_scores = [
            record.sentiment_score
            for record in batch_records
            if record.sentiment_score is not None
        ]

        return {
            "batch_id": batch_id,
            "sector_count": len(batch_records),
            "sectors": sorted(sectors),
            "timeframe": "1day",  # Implicit for SectorSentiment1D
            "timestamp": batch_records[0].timestamp.isoformat(),
            "avg_sentiment": (
                sum(sentiment_scores) / len(sentiment_scores)
                if sentiment_scores
                else 0.0
            ),
            "sentiment_range": (
                (min(sentiment_scores), max(sentiment_scores))
                if sentiment_scores
                else (0.0, 0.0)
            ),
            # Minimal schema summary (no bullish/bearish counts or total volume in 1D table)
            "total_stocks": 0,
            "total_volume": 0,
        }


# Global instance
_batch_validator: Optional[SectorBatchValidator] = None


def get_batch_validator() -> SectorBatchValidator:
    """Get global sector batch validator instance"""
    global _batch_validator
    if _batch_validator is None:
        _batch_validator = SectorBatchValidator()
    return _batch_validator
 