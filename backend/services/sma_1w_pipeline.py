"""
1W SMA Pipeline (close-to-close)
Computes 5D returns per symbol from stock_prices_1d and aggregates to sector
with simple and weighted means. Persists into sector_sentiment_1w.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List
from sqlalchemy import text

from core.database import SessionLocal
from services.sector_filters import SectorFilters
from services.sector_data_service import SectorDataService
from services.simple_sector_calculator import SectorCalculator
from models.sector_sentiment_1w import SectorSentiment1W


logger = logging.getLogger(__name__)


class SMAPipeline1W:
    def __init__(self) -> None:
        self.filters = SectorFilters()
        self.data_service = SectorDataService()
        self.calc_simple = SectorCalculator(mode="simple")
        self.calc_weighted = SectorCalculator(mode="weighted")

    async def run(self) -> Dict[str, Any]:
        sectors = self._get_sectors()
        if not sectors:
            return {"status": "no_sectors"}

        sector_results: Dict[str, Dict[str, Any]] = {}
        for sector in sectors:
            try:
                stocks = await self.data_service.get_filtered_sector_data(sector, self.filters)
                if not stocks:
                    sector_results[sector] = {"sentiment_score": 0.0, "weighted_sentiment_score": 0.0}
                    continue

                symbols = [s.get("symbol") for s in stocks if s.get("symbol")]
                if not symbols:
                    sector_results[sector] = {"sentiment_score": 0.0, "weighted_sentiment_score": 0.0}
                    continue

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
                                   MAX(price) FILTER (WHERE rn = 1) AS d0,
                                   MAX(price) FILTER (WHERE rn = 5) AS d5
                            FROM sp
                            GROUP BY symbol
                            """
                        ),
                        {"symbols": symbols},
                    ).fetchall()

                symbol_returns: List[float] = []
                weighted_input: List[Dict[str, Any]] = []
                weights_by_symbol = {str(s["symbol"]): {"price": float(s.get("current_price") or 0.0), "volume": int(s.get("volume") or 0)} for s in stocks}
                for sym, d0, d5 in rows:
                    latest = float(d0 or 0.0)
                    prior = float(d5 or 0.0)
                    if latest > 0 and prior > 0:
                        ret = ((latest - prior) / prior) * 100.0
                        symbol_returns.append(ret)
                        w = weights_by_symbol.get(str(sym), {"price": latest, "volume": 0})
                        weighted_input.append({
                            "symbol": str(sym),
                            "changes_percentage": ret,
                            "current_price": float(w.get("price") or latest),
                            "volume": int(w.get("volume") or 0),
                        })

                if symbol_returns:
                    simple = sum(symbol_returns) / len(symbol_returns)
                    weighted = self.calc_weighted.calculate_sector_performance(weighted_input)
                else:
                    simple = 0.0
                    weighted = 0.0

                sector_results[sector] = {"sentiment_score": simple, "weighted_sentiment_score": weighted}
            except Exception as e:
                logger.error(f"1W calc failed for {sector}: {e}")
                sector_results[sector] = {"sentiment_score": 0.0, "weighted_sentiment_score": 0.0}

        # Persist atomic batch
        from services.sector_batch_validator_3d import SectorBatchValidator3D  # reuse shape/logic
        validator = SectorBatchValidator3D()
        try:
            recs = []
            ok, issues = validator.validate_sector_completeness(sector_results)
            if not ok:
                raise ValueError("; ".join(issues))
            ok2, issues2 = validator.validate_sector_data_quality(sector_results)
            if not ok2:
                raise ValueError("; ".join(issues2))

            import datetime
            from datetime import timezone
            batch_id = validator.generate_batch_id().replace("batch_3d_", "batch_1w_")
            ts = datetime.datetime.now(timezone.utc)
            for s, data in sector_results.items():
                rec = SectorSentiment1W(
                    sector=s,
                    timestamp=ts,
                    batch_id=batch_id,
                    sentiment_score=float(data.get("sentiment_score", 0.0)),
                    weighted_sentiment_score=float(data.get("weighted_sentiment_score", 0.0)),
                    created_at=ts,
                )
                recs.append(rec)

            with SessionLocal() as db:
                for r in recs:
                    db.add(r)
                db.commit()

            return {"status": "success", "batch_id": batch_id, "sector_count": len(sectors)}
        except Exception as e:
            logger.error(f"1W persist failed: {e}")
            return {"status": "persist_failed"}

    def _get_sectors(self) -> List[str]:
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


_sma_pipeline_1w: SMAPipeline1W | None = None


def get_sma_pipeline_1w() -> SMAPipeline1W:
    global _sma_pipeline_1w
    if _sma_pipeline_1w is None:
        _sma_pipeline_1w = SMAPipeline1W()
    return _sma_pipeline_1w


