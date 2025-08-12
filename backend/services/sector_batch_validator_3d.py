"""
Sector Batch Validator for 3D timeframe
Ensures atomic 11-sector batches and creates SectorSentiment3D records.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import logging

from models.sector_sentiment_3d import SectorSentiment3D

logger = logging.getLogger(__name__)


class SectorBatchValidationError3D(Exception):
    pass


class SectorBatchValidator3D:
    def __init__(self):
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
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"batch_3d_{ts}_{short_uuid}"

    def validate_sector_completeness(
        self, sector_results: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        issues: List[str] = []
        if len(sector_results) != 11:
            issues.append(f"Expected 11 sectors, got {len(sector_results)}")
        provided = set(sector_results.keys())
        missing = self.expected_sectors - provided
        if missing:
            issues.append(f"Missing sectors: {sorted(missing)}")
        unexpected = provided - self.expected_sectors
        if unexpected:
            issues.append(f"Unexpected sectors: {sorted(unexpected)}")
        return len(issues) == 0, issues

    def validate_sector_data_quality(
        self, sector_results: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        issues: List[str] = []
        for sector_name, sector_data in sector_results.items():
            if not isinstance(sector_data, dict):
                issues.append(f"{sector_name}: Data is not a dictionary")
                continue
            score = sector_data.get("sentiment_score")
            if score is None:
                issues.append(f"{sector_name}: Missing sentiment_score")
            elif not isinstance(score, (int, float)):
                issues.append(f"{sector_name}: sentiment_score must be numeric")
            elif not (-100.0 <= score <= 100.0):
                issues.append(f"{sector_name}: sentiment_score out of range: {score}")
        return len(issues) == 0, issues

    def prepare_batch(
        self,
        sector_results: Dict[str, Any],
        analysis_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[SectorSentiment3D]:
        logger.info("Validating 3D sector batch")
        ok, completeness_issues = self.validate_sector_completeness(sector_results)
        if not ok:
            msg = "; ".join(completeness_issues)
            logger.error(msg)
            raise SectorBatchValidationError3D(msg)
        ok2, quality_issues = self.validate_sector_data_quality(sector_results)
        if not ok2:
            msg = "; ".join(quality_issues)
            logger.error(msg)
            raise SectorBatchValidationError3D(msg)

        batch_id = self.generate_batch_id()
        now_ts = datetime.now(timezone.utc)
        records: List[SectorSentiment3D] = []
        for sector_name, sector_data in sector_results.items():
            rec = SectorSentiment3D(
                sector=sector_name,
                timestamp=now_ts,
                batch_id=batch_id,
                sentiment_score=sector_data.get("sentiment_score", 0.0),
                created_at=now_ts,
            )
            records.append(rec)
        return records

    def get_batch_summary(self, batch_records: List[SectorSentiment3D]) -> Dict[str, Any]:
        if not batch_records:
            return {"error": "Empty batch"}
        scores = [r.sentiment_score or 0.0 for r in batch_records]
        return {
            "batch_id": batch_records[0].batch_id,
            "sector_count": len(batch_records),
            "timestamp": batch_records[0].timestamp.isoformat(),
            "avg_sentiment": (sum(scores) / len(scores)) if scores else 0.0,
        }


_validator_3d: Optional[SectorBatchValidator3D] = None


def get_batch_validator_3d() -> SectorBatchValidator3D:
    global _validator_3d
    if _validator_3d is None:
        _validator_3d = SectorBatchValidator3D()
    return _validator_3d



