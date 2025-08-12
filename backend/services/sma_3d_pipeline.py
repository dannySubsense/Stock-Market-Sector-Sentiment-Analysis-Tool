"""
3D SMA Pipeline
Reads last 3 daily closes per symbol from stock_prices_daily_ohlc view,
aggregates to sector using existing calculator semantics, and persists to sector_sentiment_3d.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from sqlalchemy import text

from core.database import SessionLocal
from services.sector_data_service import SectorDataService
from services.sector_filters import SectorFilters
from services.simple_sector_calculator import SectorCalculator
from services.data_persistence_service import get_persistence_service
from services.sector_batch_validator_3d import get_batch_validator_3d
from sqlalchemy import text

logger = logging.getLogger(__name__)


class SMAPipeline3D:
    def __init__(self, mode: str = "simple") -> None:
        self.filters = SectorFilters()
        self.data_service = SectorDataService()
        # Use explicit calculators for clarity
        self.calculator_simple = SectorCalculator(mode="simple")
        self.calculator_weighted = SectorCalculator(mode="weighted")
        self.persistence = get_persistence_service()
        self.batch_validator = get_batch_validator_3d()

    async def run(self) -> Dict[str, Any]:
        logger.info("Starting 3D SMA pipeline")

        sectors = self._get_active_sectors()
        if not sectors:
            logger.warning("No active sectors found; aborting 3D SMA pipeline")
            return {"status": "no_sectors"}

        # Build per-sector results using last-3-day symbol returns
        sector_results: Dict[str, Dict[str, Any]] = {}

        for sector in sectors:
            try:
                # Get filtered symbol list via existing data service
                stocks = await self.data_service.get_filtered_sector_data(sector, self.filters)
                if not stocks:
                    sector_results[sector] = {"sentiment_score": 0.0, "weighted_sentiment_score": 0.0}
                    continue

                # Build symbol set and a quick lookup for weights (price/volume) from latest quotes
                symbols = [s.get("symbol") for s in stocks if s.get("symbol")]
                if not symbols:
                    sector_results[sector] = {"sentiment_score": 0.0, "weighted_sentiment_score": 0.0}
                    continue
                weights_by_symbol = {str(s["symbol"]): {"price": float(s.get("current_price") or 0.0), "volume": int(s.get("volume") or 0)} for s in stocks}

                # Batch fetch last-3 closes per symbol for this sector using window function
                symbol_returns: List[float] = []
                synthetic_for_weighted: List[Dict[str, Any]] = []
                with SessionLocal() as db:
                    rows = db.execute(
                        text(
                            """
                            WITH sp AS (
                              SELECT symbol, price,
                                     ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY recorded_at DESC) AS rn
                              FROM stock_prices_1d
                              WHERE symbol = ANY(:symbols)
                            )
                            SELECT symbol,
                                   MAX(price) FILTER (WHERE rn = 1) AS latest,
                                   MAX(price) FILTER (WHERE rn = 3) AS prior
                            FROM sp
                            GROUP BY symbol
                            """
                        ),
                        {"symbols": symbols},
                    ).fetchall()

                    for sym, latest, prior in rows:
                        latest_f = float(latest or 0.0)
                        prior_f = float(prior or 0.0)
                        if latest_f > 0 and prior_f > 0:
                            ret_pct = ((latest_f - prior_f) / prior_f) * 100.0
                            symbol_returns.append(ret_pct)
                            w = weights_by_symbol.get(str(sym), {"price": latest_f, "volume": 0})
                            synthetic_for_weighted.append({
                                "symbol": str(sym),
                                "changes_percentage": ret_pct,
                                "current_price": float(w.get("price") or latest_f),
                                "volume": int(w.get("volume") or 0),
                            })

                if symbol_returns:
                    # Simple average (percent units)
                    score_simple = sum(symbol_returns) / len(symbol_returns)
                    # Weighted using explicit weighted calculator over synthetic list
                    score_weighted = self.calculator_weighted.calculate_sector_performance(synthetic_for_weighted)
                else:
                    score_simple = 0.0
                    score_weighted = 0.0

                sector_results[sector] = {
                    "sentiment_score": score_simple,
                    "weighted_sentiment_score": score_weighted,
                }

            except Exception as e:
                logger.error(f"3D SMA calculation error for sector {sector}: {e}")
                sector_results[sector] = {"sentiment_score": 0.0}

        # Validate and persist 11-sector batch to sector_sentiment_3d
        try:
            validated_batch = self.batch_validator.prepare_batch(sector_results)
        except Exception as validation_error:
            logger.error(f"3D batch validation failed: {validation_error}")
            return {"status": "persist_failed"}

        # Capture batch_id before commit to avoid attribute expiration
        batch_id_value = validated_batch[0].batch_id if validated_batch else "batch_unknown"

        with SessionLocal() as db:
            for rec in validated_batch:
                # Attach weighted score if present in sector_results
                sector_data = sector_results.get(rec.sector, {})
                ws = sector_data.get("weighted_sentiment_score")
                if ws is not None:
                    rec.weighted_sentiment_score = float(ws)
                db.add(rec)
            db.commit()

        logger.info(
            f"✅ 3D SMA pipeline completed for {len(sectors)} sectors; batch {batch_id_value}"
        )
        return {"status": "success", "batch_id": batch_id_value, "sector_count": len(sectors)}

    def _get_active_sectors(self) -> List[str]:
        # Ensure exactly the validated 11 FMP sectors to satisfy batch completeness
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


_sma_pipeline_3d: SMAPipeline3D | None = None


def get_sma_pipeline_3d() -> SMAPipeline3D:
    global _sma_pipeline_3d
    if _sma_pipeline_3d is None:
        _sma_pipeline_3d = SMAPipeline3D()
    return _sma_pipeline_3d


