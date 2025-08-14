"""
Integration test: 30m pipeline yields non-zero results when two snapshots differ
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from sqlalchemy import text

from core.database import SessionLocal
from services.sma_30m_pipeline import SMAPipeline30M


SECTOR = "utilities"
SYM_A = "T30M_A"
SYM_B = "T30M_B"


def _seed_symbol_rows(symbol: str, sector: str, ago_price: float, now_price: float) -> None:
    now = datetime.now(timezone.utc)
    ago = now - timedelta(minutes=35)
    with SessionLocal() as db:
        # Universe row
        db.execute(
            text(
                """
                INSERT INTO stock_universe(symbol, company_name, sector, market_cap, avg_daily_volume, current_price, exchange, is_active)
                VALUES (:sym, 'Test Co', :sector, 100000000, 2000000, :now_p, 'NASDAQ', true)
                ON CONFLICT (symbol) DO UPDATE SET sector = EXCLUDED.sector, is_active = true
                """
            ),
            {"sym": symbol, "sector": sector, "now_p": now_price},
        )

        # Clean prior rows for idempotency
        db.execute(text("DELETE FROM stock_prices_1d WHERE symbol = :s"), {"s": symbol})

        # Insert ago and now snapshots
        db.execute(
            text(
                """
                INSERT INTO stock_prices_1d
                (symbol, fmp_timestamp, name, price, changes_percentage, change,
                 day_low, day_high, year_high, year_low, market_cap, price_avg_50,
                 price_avg_200, exchange, volume, avg_volume, open_price, previous_close,
                 eps, pe, earnings_announcement, shares_outstanding, recorded_at)
                VALUES
                (:sym, :t_ago, 'Test Co', :ago_p, 0.0, 0.0, :ago_p, :ago_p, :ago_p, :ago_p, 0, 0, 0, 'NASD', 300000, 300000, :ago_p, :ago_p, 0, 0, NULL, 0, :ago),
                (:sym, :t_now, 'Test Co', :now_p, 0.0, 0.0, :now_p, :now_p, :now_p, :now_p, 0, 0, 0, 'NASD', 350000, 350000, :now_p, :ago_p, 0, 0, NULL, 0, :now)
                """
            ),
            {
                "sym": symbol,
                "t_ago": int(ago.timestamp()),
                "ago_p": ago_price,
                "t_now": int(now.timestamp()),
                "now_p": now_price,
                "ago": ago,
                "now": now,
            },
        )

        db.commit()


def test_sma_30m_nonzero_for_positive_moves():
    # Deactivate any pre-existing active symbols in this sector to isolate test
    with SessionLocal() as db:
        db.execute(text("UPDATE stock_universe SET is_active = false WHERE sector = :s"), {"s": SECTOR})
        db.commit()

    # Seed two symbols with positive moves
    _seed_symbol_rows(SYM_A, SECTOR, ago_price=10.0, now_price=11.0)  # +10%
    _seed_symbol_rows(SYM_B, SECTOR, ago_price=10.0, now_price=12.0)  # +20%

    # Run pipeline
    import asyncio

    asyncio.run(SMAPipeline30M().run())

    # Verify sector sentiment is > 0
    with SessionLocal() as db:
        row = db.execute(
            text(
                "SELECT sentiment_score FROM sector_sentiment_30min WHERE sector = :s ORDER BY timestamp DESC LIMIT 1"
            ),
            {"s": SECTOR},
        ).fetchone()
        assert row is not None, "Expected a 30m row for sector"
        score = float(row[0] or 0.0)
        assert score > 0.5, f"Expected positive 30m score, got {score}"


