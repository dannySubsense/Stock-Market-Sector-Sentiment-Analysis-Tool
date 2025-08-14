"""
30m SMA Pipeline (intraday)
Computes ~30-minute returns from latest and ~30m-ago snapshots in stock_prices_1d.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List
from sqlalchemy import text
from datetime import datetime, timezone, timedelta

from core.database import SessionLocal, engine
from services.simple_sector_calculator import SectorCalculator
from models.sector_sentiment_30min import SectorSentiment30M


logger = logging.getLogger(__name__)


class SMAPipeline30M:
    def __init__(self) -> None:
        self.calc_weighted = SectorCalculator(mode="weighted")

    async def run(self) -> Dict[str, Any]:
        sectors = self._get_sectors()
        if not sectors:
            return {"status": "no_sectors"}

        sector_results: Dict[str, Dict[str, Any]] = {}
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=30)
        tolerance = timedelta(minutes=5)
        cutoff_plus = cutoff + tolerance

        for sector in sectors:
            try:
                with SessionLocal() as db:
                    # Active symbols for this sector
                    symbols = [
                        r[0]
                        for r in db.execute(
                            text("SELECT symbol FROM stock_universe WHERE sector = :sector AND is_active = true"),
                            {"sector": sector},
                        ).fetchall()
                    ]
                    if not symbols:
                        sector_results[sector] = {"sentiment_score": 0.0, "weighted_sentiment_score": 0.0}
                        continue

                    # Latest snapshot and strict ago snapshot (must be at least 25 minutes older than latest per symbol)
                    rows = db.execute(
                        text(
                            """
                            WITH latest AS (
                              SELECT symbol, price AS now_price, volume AS now_volume, recorded_at AS now_ts,
                                     ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY recorded_at DESC) AS rn
                              FROM stock_prices_1d WHERE symbol = ANY(:symbols)
                            ),
                            picked_latest AS (
                              SELECT symbol, now_price, now_volume, now_ts FROM latest WHERE rn = 1
                            ),
                            ago AS (
                              SELECT sp.symbol, sp.price AS ago_price,
                                     ROW_NUMBER() OVER (PARTITION BY sp.symbol ORDER BY sp.recorded_at DESC) AS arn
                              FROM stock_prices_1d sp
                              JOIN picked_latest pl ON pl.symbol = sp.symbol
                              WHERE sp.symbol = ANY(:symbols)
                                AND sp.recorded_at <= (pl.now_ts - INTERVAL '25 minutes')
                            )
                            SELECT pl.symbol,
                                   pl.now_price AS now_price,
                                   pl.now_volume AS now_volume,
                                   MAX(a.ago_price) FILTER (WHERE a.arn = 1) AS ago_price
                            FROM picked_latest pl
                            LEFT JOIN ago a ON a.symbol = pl.symbol
                            GROUP BY pl.symbol, pl.now_price, pl.now_volume
                            """
                        ),
                        {"symbols": symbols},
                    ).fetchall()

                symbol_returns: List[float] = []
                weighted_input: List[Dict[str, Any]] = []
                for sym, now_price, now_volume, ago_price in rows:
                    latest = float(now_price or 0.0)
                    prior = float(ago_price or 0.0)
                    vol = int(now_volume or 0)
                    if latest > 0 and prior > 0:
                        ret = ((latest - prior) / prior) * 100.0
                        symbol_returns.append(ret)
                        weighted_input.append({
                            "symbol": str(sym),
                            "changes_percentage": ret,
                            "current_price": latest,
                            "volume": vol,
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

            ts = now
            batch_id = validator.generate_batch_id().replace("batch_3d_", "batch_30m_")
            # Ensure destination table exists (dev environments may not run migrations)
            try:
                SectorSentiment30M.__table__.create(bind=engine, checkfirst=True)
            except Exception:
                pass
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


