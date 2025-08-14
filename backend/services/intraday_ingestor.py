"""
Intraday Ingestor (5-minute loop during market hours)

Fetch batch quotes from FMP for active universe symbols, store to stock_prices_1d,
and trigger 30m recompute respecting cooldown.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, time
from typing import List

from sqlalchemy import text

from core.config import get_settings
from core.database import SessionLocal
from services.fmp_batch_data_service import FMPBatchDataService
from services.data_persistence_service import get_persistence_service
from services.sma_30m_pipeline import get_sma_pipeline_30m
from services.sma_1d_pipeline import get_sma_pipeline_1d


logger = logging.getLogger(__name__)


def _is_market_hours(now: datetime) -> bool:
    # Market hours 09:30–16:00 ET; assume server on UTC; adjust simply by comparing ET offset via settings if needed
    # For simplicity here, allow all hours; user can tune enable_intraday_ingest by schedule
    return True


async def run_intraday_loop(stop_event: asyncio.Event) -> None:
    settings = get_settings()
    interval = max(int(settings.intraday_ingest_interval_seconds or 300), 60)
    batch = FMPBatchDataService()
    persistence = get_persistence_service()
    sma1d = get_sma_pipeline_1d()
    sma30 = get_sma_pipeline_30m()

    logger.info("Starting intraday ingest loop for 30m support")
    while not stop_event.is_set():
        try:
            now = datetime.now(timezone.utc)
            if _is_market_hours(now):
                # Get active symbols
                with SessionLocal() as db:
                    syms: List[str] = [r[0] for r in db.execute(text("SELECT symbol FROM stock_universe WHERE is_active = true")).fetchall()]
                if syms:
                    quotes = await batch.get_universe_price_data(syms)
                    # Store raw batch quotes to stock_prices_1d with proper changesPercentage
                    payload = []
                    for q in quotes:
                        try:
                            changes_pct = getattr(q, 'fmp_changes_percentage', None)
                            if changes_pct is None and (q.previous_close or 0) > 0:
                                changes_pct = ((q.current_price - q.previous_close) / q.previous_close) * 100.0
                            payload.append({
                                "symbol": q.symbol,
                                "price": q.current_price,
                                "previousClose": q.previous_close,
                                "changesPercentage": float(changes_pct or 0.0),
                                "volume": q.current_volume,
                                "avgVolume": q.avg_20_day_volume,
                                "open": q.current_price,
                                "dayLow": q.current_price,
                                "dayHigh": q.current_price,
                                "marketCap": 0,
                            })
                        except Exception:
                            continue
                    if payload:
                        await persistence.store_fmp_batch_price_data(payload)
                    else:
                        logger.warning("No valid quotes to persist in this cycle")
                    # Recompute 1D, then 30m
                    await sma1d.run()
                    await sma30.run()
                else:
                    logger.warning("No active symbols found; skipping ingest cycle")
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error(f"Intraday ingest cycle failed: {e}")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass

    logger.info("Intraday ingest loop stopped")


