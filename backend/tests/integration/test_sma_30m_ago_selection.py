"""
Integration test: 30m pipeline must exclude symbols whose 'ago' snapshot is too recent

Validates strict selection: ago <= latest_ts - 25 minutes
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import asyncio

from sqlalchemy import text

from core.database import SessionLocal
from services.sma_30m_pipeline import SMAPipeline30M


SECTOR = "utilities"
SYM_RECENT = "UTILREC30"   # <= 10 chars
SYM_VALID = "UTILVAL30"    # <= 10 chars


def _seed_data() -> tuple[float, float]:
    now = datetime.now(timezone.utc)
    ago_20 = now - timedelta(minutes=20)
    ago_35 = now - timedelta(minutes=35)

    # Prices: recent symbol moves +10%, valid symbol moves +20%
    recent_ago_price = 10.0
    recent_now_price = 11.0
    valid_ago_price = 10.0
    valid_now_price = 12.0

    with SessionLocal() as db:
        # Isolate the sector: deactivate pre-existing actives
        db.execute(text("UPDATE stock_universe SET is_active = false WHERE sector = :s"), {"s": SECTOR})

        # Ensure universe rows for our symbols
        for sym, now_p in [
            (SYM_RECENT, recent_now_price),
            (SYM_VALID, valid_now_price),
        ]:
            db.execute(
                text(
                    """
                    INSERT INTO stock_universe(symbol, company_name, sector, market_cap, avg_daily_volume, current_price, exchange, is_active)
                    VALUES (:sym, 'Test Co', :sector, 100000000, 2000000, :now_p, 'NASDAQ', true)
                    ON CONFLICT (symbol) DO UPDATE SET sector = EXCLUDED.sector, is_active = true
                    """
                ),
                {"sym": sym, "sector": SECTOR, "now_p": now_p},
            )

        # Clean prior price rows for idempotency
        db.execute(text("DELETE FROM stock_prices_1d WHERE symbol IN (:a, :b)"), {"a": SYM_RECENT, "b": SYM_VALID})

        # Insert snapshots for RECENT (ago only 20m before now → should be excluded by 25m rule)
        db.execute(
            text(
                """
                INSERT INTO stock_prices_1d
                (symbol, fmp_timestamp, name, price, changes_percentage, change,
                 day_low, day_high, year_high, year_low, market_cap, price_avg_50,
                 price_avg_200, exchange, volume, avg_volume, open_price, previous_close,
                 eps, pe, earnings_announcement, shares_outstanding, recorded_at)
                VALUES
                (:sym, :t_ago, 'Recent', :ago_p, 0.0, 0.0, :ago_p, :ago_p, :ago_p, :ago_p, 0, 0, 0, 'NASD', 300000, 300000, :ago_p, :ago_p, 0, 0, NULL, 0, :ago),
                (:sym, :t_now, 'Recent', :now_p, 0.0, 0.0, :now_p, :now_p, :now_p, :now_p, 0, 0, 0, 'NASD', 350000, 350000, :now_p, :ago_p, 0, 0, NULL, 0, :now)
                """
            ),
            {
                "sym": SYM_RECENT,
                "t_ago": int(ago_20.timestamp()),
                "ago_p": recent_ago_price,
                "t_now": int(now.timestamp()),
                "now_p": recent_now_price,
                "ago": ago_20,
                "now": now,
            },
        )

        # Insert snapshots for VALID (ago 35m before now → should be included)
        db.execute(
            text(
                """
                INSERT INTO stock_prices_1d
                (symbol, fmp_timestamp, name, price, changes_percentage, change,
                 day_low, day_high, year_high, year_low, market_cap, price_avg_50,
                 price_avg_200, exchange, volume, avg_volume, open_price, previous_close,
                 eps, pe, earnings_announcement, shares_outstanding, recorded_at)
                VALUES
                (:sym, :t_ago, 'Valid', :ago_p, 0.0, 0.0, :ago_p, :ago_p, :ago_p, :ago_p, 0, 0, 0, 'NASD', 300000, 300000, :ago_p, :ago_p, 0, 0, NULL, 0, :ago),
                (:sym, :t_now, 'Valid', :now_p, 0.0, 0.0, :now_p, :now_p, :now_p, :now_p, 0, 0, 0, 'NASD', 360000, 360000, :now_p, :ago_p, 0, 0, NULL, 0, :now)
                """
            ),
            {
                "sym": SYM_VALID,
                "t_ago": int(ago_35.timestamp()),
                "ago_p": valid_ago_price,
                "t_now": int(now.timestamp()),
                "now_p": valid_now_price,
                "ago": ago_35,
                "now": now,
            },
        )

        db.commit()

    # Return expected valid return percent
    expected_valid = ((valid_now_price - valid_ago_price) / valid_ago_price) * 100.0
    return expected_valid, now.timestamp()


def test_sma_30m_strict_ago_selection_excludes_recent():
    expected_valid, _ = _seed_data()

    # Run 30m pipeline
    asyncio.run(SMAPipeline30M().run())

    # Validate: sector row exists and equals the valid symbol's return (recent excluded)
    with SessionLocal() as db:
        row = db.execute(
            text(
                "SELECT sentiment_score FROM sector_sentiment_30min WHERE sector = :s ORDER BY timestamp DESC LIMIT 1"
            ),
            {"s": SECTOR},
        ).fetchone()
        assert row is not None, "Expected a 30m row for sector"
        score = float(row[0] or 0.0)
        # Tolerance 0.01%
        assert abs(score - expected_valid) < 0.01, f"Expected ~{expected_valid:.2f}%, got {score:.4f}%"


