from datetime import datetime, timedelta, timezone
from sqlalchemy import text

from core.database import SessionLocal
from services.sma_3d_pipeline import get_sma_pipeline_3d


def _seed_prices(symbol: str, closes: list[float]) -> None:
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        rows = []
        for i, close in enumerate(closes):
            ts = now - timedelta(days=i)
            rows.append(
                {
                    "symbol": symbol,
                    "fmp_timestamp": int(ts.timestamp()),
                    "name": None,
                    "price": close,
                    "changes_percentage": None,
                    "change": None,
                    "day_low": close,
                    "day_high": close,
                    "year_high": None,
                    "year_low": None,
                    "market_cap": None,
                    "price_avg_50": None,
                    "price_avg_200": None,
                    "exchange": None,
                    "volume": 1000,
                    "avg_volume": None,
                    "open_price": close,
                    "previous_close": None,
                    "eps": None,
                    "pe": None,
                    "earnings_announcement": None,
                    "shares_outstanding": None,
                    "recorded_at": ts,
                }
            )
        db.execute(
            text(
                """
                INSERT INTO stock_prices_1d (
                    symbol, fmp_timestamp, name, price, changes_percentage, change,
                    day_low, day_high, year_high, year_low, market_cap, price_avg_50,
                    price_avg_200, exchange, volume, avg_volume, open_price, previous_close,
                    eps, pe, earnings_announcement, shares_outstanding, recorded_at
                ) VALUES (
                    :symbol, :fmp_timestamp, :name, :price, :changes_percentage, :change,
                    :day_low, :day_high, :year_high, :year_low, :market_cap, :price_avg_50,
                    :price_avg_200, :exchange, :volume, :avg_volume, :open_price, :previous_close,
                    :eps, :pe, :earnings_announcement, :shares_outstanding, :recorded_at
                ) ON CONFLICT (symbol, fmp_timestamp) DO NOTHING
                """
            ),
            rows,
        )
        db.commit()


def test_sma_3d_pipeline_persists_batch():
    # Seed two tech symbols with a rising pattern so the average is positive
    _seed_prices("TESTA", [10.0, 9.5, 9.0])  # +11.11% over 3 bars
    _seed_prices("TESTB", [20.0, 19.0, 18.0])  # +11.11% over 3 bars

    # Run pipeline
    import asyncio

    result = asyncio.run(get_sma_pipeline_3d().run())
    assert result.get("status") == "success"


