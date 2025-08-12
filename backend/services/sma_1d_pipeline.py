"""
Validated 1D SMA Pipeline (Production)

Implements the exact validated 1-day pattern using:
- DB-based data retrieval via SectorDataService with SQL filters
- Simple average via SectorCalculator
- Atomic 11-sector batch persistence into sector_sentiment_1d (minimal schema)
- Separate storage of top gainers/losers into sector_gappers_1d

This module is intentionally independent of per-symbol API retrieval.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from core.database import SessionLocal
from sqlalchemy import text
from services.sector_data_service import SectorDataService
from services.simple_sector_calculator import SectorCalculator
from services.sector_filters import SectorFilters
from services.data_persistence_service import get_persistence_service
from services.sector_batch_validator import get_batch_validator
from models.sector_gappers_1d import SectorGappers1D, GapperType

logger = logging.getLogger(__name__)


class SMAPipeline1D:
    def __init__(self, mode: str = "simple") -> None:
        self.filters = SectorFilters()
        self.data_service = SectorDataService()
        self.calculator = SectorCalculator(mode=mode)
        self.persistence = get_persistence_service()
        self.batch_validator = get_batch_validator()

    async def run(self) -> Dict[str, Any]:
        """
        Execute the validated 1D SMA pipeline end-to-end.
        Returns metadata with batch id and counts.
        """
        logger.info("Starting validated 1D SMA pipeline (production)")

        # 1) Discover active sectors
        sectors = self._get_active_sectors()
        if not sectors:
            logger.warning("No active sectors found in universe; aborting 1D SMA pipeline")
            return {"status": "no_sectors"}

        # 2) Build per-sector results using DB-based data + simple average
        sector_results: Dict[str, Dict[str, Any]] = {}
        per_sector_gappers: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

        for sector in sectors:
            try:
                stocks = await self.data_service.get_filtered_sector_data(sector, self.filters)
                if not stocks:
                    logger.info(f"No stocks found for sector {sector} with current filters; using 0.0")
                    sector_results[sector] = {"sentiment_score": 0.0}
                    per_sector_gappers[sector] = {"top_gainers": [], "top_losers": []}
                    continue

                performance = self.calculator.calculate_sector_performance(stocks)
                rankings = self.calculator.get_top_gainers_losers(stocks)

                sector_results[sector] = {"sentiment_score": performance}
                per_sector_gappers[sector] = rankings

            except Exception as e:
                logger.error(f"1D SMA calculation error for sector {sector}: {e}")
                sector_results[sector] = {"sentiment_score": 0.0}
                per_sector_gappers[sector] = {"top_gainers": [], "top_losers": []}

        # 3) Validate and persist 11-sector batch to sector_sentiment_1d (minimal schema)
        #    Use batch validator to generate batch_id and records via persistence service
        persist_ok = await self.persistence.store_sector_sentiment_data(sector_results, analysis_metadata={"pipeline": "sma_1d"})
        if not persist_ok:
            logger.error("Failed to persist 1D SMA batch to sector_sentiment_1d")
            return {"status": "persist_failed"}

        # 4) Persist gappers to sector_gappers_1d (separate table)
        batch_id, timestamp = self._get_latest_1d_batch_meta()
        await self._store_gappers(per_sector_gappers, batch_id, timestamp)

        logger.info(f"✅ 1D SMA pipeline completed for {len(sectors)} sectors; batch {batch_id}")
        return {"status": "success", "batch_id": batch_id, "sector_count": len(sectors)}

    def _get_active_sectors(self) -> List[str]:
        with SessionLocal() as db:
            rows = db.execute(
                text("SELECT DISTINCT sector FROM stock_universe WHERE is_active = true ORDER BY sector")
            ).fetchall()
            sectors = [row[0] for row in rows]
            if sectors:
                return sectors
            # Fallback to validated 11 FMP sectors if universe is empty
            return [
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
            ]

    def _get_latest_1d_batch_meta(self) -> (str, datetime):
        """Fetch latest batch_id and timestamp from sector_sentiment_1d after persistence."""
        from models.sector_sentiment_1d import SectorSentiment1D
        from sqlalchemy import desc
        with SessionLocal() as db:
            rec = (
                db.query(SectorSentiment1D)
                .order_by(desc(SectorSentiment1D.timestamp))
                .first()
            )
            if not rec:
                # Fallback
                return "batch_unknown", datetime.now(timezone.utc)
            return rec.batch_id, rec.timestamp

    async def _store_gappers(self, per_sector_gappers: Dict[str, Dict[str, List[Dict[str, Any]]]], batch_id: str, ts: datetime) -> None:
        with SessionLocal() as db:
            for sector, rankings in per_sector_gappers.items():
                # Gainers
                for rank, g in enumerate(rankings.get("top_gainers", []), 1):
                    db.add(
                        SectorGappers1D(
                            sector=sector,
                            timestamp=ts,
                            gapper_type=GapperType.GAINER.value,
                            rank=rank,
                            batch_id=batch_id,
                            symbol=g.get("symbol", ""),
                            changes_percentage=float(g.get("changes_percentage", 0.0)),
                            volume=int(g.get("volume", 0)),
                            current_price=float(g.get("current_price", 0.0)),
                            created_at=datetime.now(timezone.utc),
                        )
                    )
                # Losers
                for rank, l in enumerate(rankings.get("top_losers", []), 1):
                    db.add(
                        SectorGappers1D(
                            sector=sector,
                            timestamp=ts,
                            gapper_type=GapperType.LOSER.value,
                            rank=rank,
                            batch_id=batch_id,
                            symbol=l.get("symbol", ""),
                            changes_percentage=float(l.get("changes_percentage", 0.0)),
                            volume=int(l.get("volume", 0)),
                            current_price=float(l.get("current_price", 0.0)),
                            created_at=datetime.now(timezone.utc),
                        )
                    )
            db.commit()


# Convenience accessor
_sma_pipeline_1d: SMAPipeline1D | None = None


def get_sma_pipeline_1d() -> SMAPipeline1D:
    global _sma_pipeline_1d
    if _sma_pipeline_1d is None:
        _sma_pipeline_1d = SMAPipeline1D()
    return _sma_pipeline_1d

