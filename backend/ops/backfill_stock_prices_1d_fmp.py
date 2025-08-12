#!/usr/bin/env python3
"""
Backfill historical daily prices into stock_prices_1d using FMP historical-price-full.

Assumptions:
- Symbols come from existing `stock_universe` table (is_active = true).
- Maps FMP fields to our schema:
  open  -> open_price
  high  -> day_high
  low   -> day_low
  close -> price (used as close)
  volume -> volume
  date  -> fmp_timestamp (epoch seconds) and recorded_at (UTC)

Idempotent:
- Uses ON CONFLICT DO NOTHING on (symbol, fmp_timestamp) primary key.

Usage (PowerShell):
  cd backend; python ops\backfill_stock_prices_1d_fmp.py --days 14
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from sqlalchemy import text

# Ensure 'backend' directory is on sys.path so imports resolve from repo root or backend/
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.database import SessionLocal
from mcp.fmp_client import get_fmp_client


def get_active_symbols() -> List[str]:
    symbols: List[str] = []
    with SessionLocal() as db:
        rows = db.execute(
            text("SELECT symbol FROM stock_universe WHERE is_active = true")
        ).fetchall()
        symbols = [r[0] for r in rows]
    return symbols


def parse_fmp_date_to_dt(date_str: str) -> datetime:
    # FMP uses YYYY-MM-DD; interpret as midnight UTC
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return dt


def build_insert_rows(symbol: str, bars: List[Dict[str, Any]], start_dt_utc: datetime) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for bar in bars:
        date_s = bar.get("date") or bar.get("label")
        if not date_s:
            continue
        dt_utc = parse_fmp_date_to_dt(str(date_s))
        # Respect days range
        if dt_utc < start_dt_utc:
            continue
        # Map fields with safe defaults
        open_price = float(bar.get("open") or 0.0)
        high_price = float(bar.get("high") or 0.0)
        low_price = float(bar.get("low") or 0.0)
        close_price = float(bar.get("close") or 0.0)
        volume = int(bar.get("volume") or 0)
        if close_price <= 0 and open_price <= 0:
            # Skip empty bars
            continue
        rows.append(
            {
                "symbol": symbol.upper(),
                "fmp_timestamp": int(dt_utc.timestamp()),
                "name": None,
                "price": close_price,
                "changes_percentage": None,
                "change": None,
                "day_low": low_price,
                "day_high": high_price,
                "year_high": None,
                "year_low": None,
                "market_cap": None,
                "price_avg_50": None,
                "price_avg_200": None,
                "exchange": None,
                "volume": volume,
                "avg_volume": None,
                "open_price": open_price,
                "previous_close": None,
                "eps": None,
                "pe": None,
                "earnings_announcement": None,
                "shares_outstanding": None,
                "recorded_at": dt_utc,
            }
        )
    return rows


async def backfill(days: int) -> None:
    fmp = get_fmp_client()

    # Determine date range
    to_dt_utc = datetime.now(timezone.utc)
    from_dt_utc = to_dt_utc - timedelta(days=days)
    from_date = from_dt_utc.strftime("%Y-%m-%d")
    to_date = to_dt_utc.strftime("%Y-%m-%d")

    symbols = get_active_symbols()
    print(f"Found {len(symbols)} active symbols to backfill ({days} days): {from_date}..{to_date}")

    inserted_total = 0
    skipped_total = 0

    # Prepare insert SQL
    insert_sql = text(
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
        )
        ON CONFLICT (symbol, fmp_timestamp) DO NOTHING
        """
    )

    with SessionLocal() as db:
        for idx, symbol in enumerate(symbols, 1):
            try:
                resp = await fmp.get_historical_prices(symbol, from_date, to_date)
                if resp.get("status") != "success":
                    print(f"WARN {symbol}: API error {resp.get('message')}")
                    continue
                bars = resp.get("historical", [])
                rows = build_insert_rows(symbol, bars, from_dt_utc)
                if not rows:
                    skipped_total += 1
                    continue
                db.execute(insert_sql, rows)
                db.commit()
                inserted_total += len(rows)
                if idx % 50 == 0:
                    print(f"… processed {idx} symbols; inserted rows so far: {inserted_total}")
            except Exception as e:
                print(f"ERROR {symbol}: {e}")
                db.rollback()

    print(f"Done. Inserted {inserted_total} rows; skipped {skipped_total} symbols with no rows.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill FMP historical daily prices into stock_prices_1d")
    parser.add_argument("--days", type=int, default=14, help="How many calendar days back to fetch")
    args = parser.parse_args()

    import asyncio

    asyncio.run(backfill(args.days))


if __name__ == "__main__":
    main()


