"""
30m SMA Pipeline (intraday)
Computes ~30-minute returns from latest and ~30m-ago snapshots in stock_prices_1d.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List
from sqlalchemy import text
from datetime import datetime, timezone, timedelta

from core.database import SessionLocal
from services.sector_filters import SectorFilters
from services.sector_data_service import SectorDataService
from services.simple_sector_calculator import SectorCalculator
from models.sector_sentiment_30min import SectorSentiment30M


logger = logging.getLogger(__name__)


class SMAPipeline30M:
    def __init__(self) -> None:
        self.filters = SectorFilters()
        self.data_service = SectorDataService()
        self.calc_weighted = SectorCalculator(mode="weighted")

    async def run(self) -> Dict[str, Any]:
        sectors = self._get_sectors()
        if not sectors:
            return {"status": "no_sectors"}

        sector_results: Dict[str, Dict[str, Any]] = {}
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=30)

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
                    # Latest and ~30m ago snapshots per symbol
                    rows = db.execute(
                        text(
                            """
                            WITH latest AS (
                              SELECT symbol, price,
                                     ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY recorded_at DESC) AS rn
                              FROM stock_prices_1d WHERE symbol = ANY(:symbols)
                            ),
                            ago AS (
                              SELECT symbol, price,
                                     ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY recorded_at DESC) AS rn
                              FROM stock_prices_1d
                              WHERE symbol = ANY(:symbols) AND recorded_at <= :cutoff
                            )
                            SELECT l.symbol,
                                   MAX(l.price) FILTER (WHERE l.rn = 1) AS now_price,
                                   MAX(a.price) FILTER (WHERE a.rn = 1) AS ago_price
                            FROM latest l
                            LEFT JOIN ago a ON a.symbol = l.symbol
                            GROUP BY l.symbol
                            """
                        ),
                        {"symbols": symbols, "cutoff": cutoff},
                    ).fetchall()

                symbol_returns: List[float] = []
                weighted_input: List[Dict[str, Any]] = []
                weights_by_symbol = {str(s["symbol"]): {"price": float(s.get("current_price") or 0.0), "volume": int(s.get("volume") or 0)} for s in stocks}
                for sym, now_price, ago_price in rows:
                    latest = float(now_price or 0.0)
                    prior = float(ago_price or 0.0)
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
                logger.error(f"30m calc failed for {sector}: {e}")
                sector_results[sector] = {"sentiment_score": 0.0, "weighted_sentiment_score": 0.0}

        # Persist batch
        from services.sector_batch_validator_3d import SectorBatchValidator3D
        validator = SectorBatchValidator3D()
        try:
            ok, issues = validator.validate_sector_completeness(sector_results)
            if not ok:
                raise ValueError("; ".join(issues))
            ok2, issues2 = validator.validate_sector_data_quality(sector_results)
            if not ok2:
                raise ValueError("; ".join(issues2))

            import datetime
            ts = now
            batch_id = validator.generate_batch_id().replace("batch_3d_", "batch_30m_")
            with SessionLocal() as db:
                for s, data in sector_results.items():
                    db.add(
                        SectorSentiment30M(
                            sector=s,
                            timestamp=ts,
                            batch_id=batch_id,
                            sentiment_score=float(data.get("sentiment_score", 0.0)),
                            weighted_sentiment_score=float(data.get("weighted_sentiment_score", 0.0)),
                            created_at=ts,
                        )
                    )
                db.commit()
            return {"status": "success", "batch_id": batch_id, "sector_count": len(sectors)}
        except Exception as e:
            logger.error(f"30m persist failed: {e}")
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


_sma_pipeline_30m: SMAPipeline30M | None = None


def get_sma_pipeline_30m() -> SMAPipeline30M:
    global _sma_pipeline_30m
    if _sma_pipeline_30m is None:
        _sma_pipeline_30m = SMAPipeline30M()
    return _sma_pipeline_30m


