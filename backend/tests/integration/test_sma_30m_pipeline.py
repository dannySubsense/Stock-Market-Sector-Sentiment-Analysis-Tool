"""
Integration tests for 30-minute SMA pipeline

Seeds minimal data into stock_universe and stock_prices_1d,
runs the 30m pipeline, and verifies persistence and API response.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Any

import asyncio
import math

from sqlalchemy import text

from core.database import SessionLocal
from services.sma_30m_pipeline import SMAPipeline30M
from fastapi.testclient import TestClient
from main import app


TEST_SECTOR = "technology"
SYM1 = "TST30M1"
SYM2 = "TST30M2"


def _seed_minimal_30m_data() -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    ago = now - timedelta(minutes=35)

    with SessionLocal() as db:
        # Ensure universe rows
        db.execute(
            text(
                """
                INSERT INTO stock_universe(symbol, company_name, sector, market_cap, avg_daily_volume, current_price, exchange, is_active)
                VALUES (:s1, 'Test Co 1', :sector, 100000000, 2000000, 10.0, 'NASDAQ', true)
                ON CONFLICT (symbol) DO UPDATE SET sector = EXCLUDED.sector, is_active = true;
                """
            ),
            {"s1": SYM1, "sector": TEST_SECTOR},
        )
        db.execute(
            text(
                """
                INSERT INTO stock_universe(symbol, company_name, sector, market_cap, avg_daily_volume, current_price, exchange, is_active)
                VALUES (:s2, 'Test Co 2', :sector, 120000000, 2500000, 10.0, 'NASDAQ', true)
                ON CONFLICT (symbol) DO UPDATE SET sector = EXCLUDED.sector, is_active = true;
                """
            ),
            {"s2": SYM2, "sector": TEST_SECTOR},
        )

        # Clean any existing price rows for our symbols
        db.execute(text("DELETE FROM stock_prices_1d WHERE symbol IN (:a,:b)"), {"a": SYM1, "b": SYM2})

        # Insert 35 minutes ago snapshots
        db.execute(
            text(
                """
                INSERT INTO stock_prices_1d
                (symbol, fmp_timestamp, name, price, changes_percentage, change,
                 day_low, day_high, year_high, year_low, market_cap, price_avg_50,
                 price_avg_200, exchange, volume, avg_volume, open_price, previous_close,
                 eps, pe, earnings_announcement, shares_outstanding, recorded_at)
                VALUES
                (:s1, :t_ago, 'Test Co 1', 10.00, 0.0, 0.0, 9.5, 10.5, 10.5, 9.0, 0, 0, 0, 'NASD', 300000, 300000, 10.0, 10.0, 0, 0, NULL, 0, :ago),
                (:s2, :t_ago, 'Test Co 2', 10.00, 0.0, 0.0, 9.5, 10.5, 10.5, 9.0, 0, 0, 0, 'NASD', 400000, 400000, 10.0, 10.0, 0, 0, NULL, 0, :ago)
                """
            ),
            {"s1": SYM1, "s2": SYM2, "ago": ago, "t_ago": int(ago.timestamp())},
        )

        # Insert latest snapshots
        db.execute(
            text(
                """
                INSERT INTO stock_prices_1d
                (symbol, fmp_timestamp, name, price, changes_percentage, change,
                 day_low, day_high, year_high, year_low, market_cap, price_avg_50,
                 price_avg_200, exchange, volume, avg_volume, open_price, previous_close,
                 eps, pe, earnings_announcement, shares_outstanding, recorded_at)
                VALUES
                (:s1, :t_now, 'Test Co 1', 10.50, 5.0, 0.5, 9.5, 10.8, 10.8, 9.0, 0, 0, 0, 'NASD', 350000, 350000, 10.0, 10.0, 0, 0, NULL, 0, :now),
                (:s2, :t_now, 'Test Co 2', 9.50, -5.0, -0.5, 9.0, 10.6, 10.6, 8.8, 0, 0, 0, 'NASD', 450000, 450000, 10.0, 10.0, 0, 0, NULL, 0, :now)
                """
            ),
            {"s1": SYM1, "s2": SYM2, "now": now, "t_now": int(now.timestamp())},
        )

        db.commit()

    return {"now": now, "ago": ago}


def test_sma_30m_persists_and_api_serves():
    _seed_minimal_30m_data()

    # Run pipeline
    asyncio.run(SMAPipeline30M().run())

    # Verify persistence
    with SessionLocal() as db:
        cnt = db.execute(text("SELECT COUNT(*) FROM sector_sentiment_30min")).scalar()
        assert cnt and cnt >= 11
        row = db.execute(
            text("SELECT sentiment_score FROM sector_sentiment_30min WHERE sector = :s ORDER BY timestamp DESC LIMIT 1"),
            {"s": TEST_SECTOR},
        ).fetchone()
        assert row is not None
        score = float(row[0] or 0.0)
        # Expect roughly average of +5% and -5% = 0%
        assert -0.1 <= score <= 0.1

    # Verify API
    with TestClient(app) as client:
        r = client.get("/api/sectors/30min/")
        assert r.status_code == 200
        data = r.json()
        assert "sectors" in data and isinstance(data["sectors"], list)
        tech = next((s for s in data["sectors"] if s.get("sector") == TEST_SECTOR), None)
        assert tech is not None
        # normalized ~ 0.0
        assert abs(float(tech.get("sentiment_normalized", 0.0))) <= 0.005


