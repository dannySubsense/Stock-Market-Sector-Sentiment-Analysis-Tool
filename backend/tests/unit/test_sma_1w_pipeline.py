from datetime import datetime, timedelta, timezone
from sqlalchemy import text

from core.database import SessionLocal
from services.sma_1w_pipeline import get_sma_pipeline_1w


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
                    "year_high": close,
                    "year_low": close,
                    "market_cap": 0,
                    "price_avg_50": 0,
                    "price_avg_200": 0,
                    "exchange": None,
                    "volume": 1_000_000,
                    "avg_volume": 1_000_000,
                    "open_price": close,
                    "previous_close": close,
                    "eps": 0,
                    "pe": 0,
                    "earnings_announcement": None,
                    "shares_outstanding": 0,
                    "recorded_at": ts,
                }
            )
        db.execute(
            text(
                """
                INSERT INTO stock_prices_1d
                (symbol, fmp_timestamp, name, price, changes_percentage, change,
                 day_low, day_high, year_high, year_low, market_cap, price_avg_50,
                 price_avg_200, exchange, volume, avg_volume, open_price, previous_close,
                 eps, pe, earnings_announcement, shares_outstanding, recorded_at)
                VALUES (:symbol, :fmp_timestamp, :name, :price, :changes_percentage, :change,
                        :day_low, :day_high, :year_high, :year_low, :market_cap, :price_avg_50,
                        :price_avg_200, :exchange, :volume, :avg_volume, :open_price, :previous_close,
                        :eps, :pe, :earnings_announcement, :shares_outstanding, :recorded_at)
                """
            ),
            rows,
        )
        db.commit()


def test_sma_1w_pipeline_persists_batch():
    # Seed two symbols with 5 days of closes
    _seed_prices("AAA", [100, 99, 98, 97, 96])
    _seed_prices("BBB", [50, 49, 48, 47, 46])

    # Run pipeline
    import asyncio

    result = asyncio.get_event_loop().run_until_complete(get_sma_pipeline_1w().run())
    assert result["status"] == "success"
    assert result["sector_count"] == 11

