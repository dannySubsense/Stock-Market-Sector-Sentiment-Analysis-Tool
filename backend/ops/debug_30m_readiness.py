"""
Debug 30m Readiness

Run:  python backend/ops/debug_30m_readiness.py

Prints whether the database currently has enough data to compute 30-minute sector metrics
and highlights the first sector that should work (symbols with both now and ~30m-ago prices).
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from sqlalchemy import text

from core.database import SessionLocal
from services.sector_data_service import SectorDataService
from services.sector_filters import SectorFilters


SECTORS = [
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


def main() -> None:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=30)
    cutoff_plus = cutoff + timedelta(minutes=5)

    with SessionLocal() as db:
        row = db.execute(
            text("SELECT MIN(recorded_at) AS mn, MAX(recorded_at) AS mx, COUNT(*) AS cnt FROM stock_prices_1d")
        ).fetchone()
        mn = row.mn
        mx = row.mx
        cnt = int(row.cnt or 0)
        span = (mx - mn).total_seconds() / 60 if (mx and mn) else 0
        print(f"stock_prices_1d: count={cnt}, span_minutes={span:.1f}, min={mn}, max={mx}")

        # Universe by sector
        uni = db.execute(
            text(
                "SELECT sector, COUNT(*) AS n FROM stock_universe WHERE is_active = true GROUP BY sector ORDER BY sector"
            )
        ).fetchall()
        print("active_universe:")
        for r in uni:
            print(f"  {r.sector}: {int(r.n or 0)}")

    # Check filtered symbol availability per sector (uses latest rows)
    svc = SectorDataService()
    filters = SectorFilters()
    # Relax 30m min volume for breadth
    try:
        filters.volume.min_volume = 50_000
    except Exception:
        pass

    candidate_sector: str | None = None
    candidate_symbols: List[str] = []
    for s in SECTORS:
        stocks = []
        try:
            stocks = __import__("asyncio").run(svc.get_filtered_sector_data(s, filters))  # sync run
        except RuntimeError:
            # Running inside an event loop (rare for CLI); fall back to direct call
            import asyncio
            stocks = asyncio.get_event_loop().run_until_complete(svc.get_filtered_sector_data(s, filters))
        n = len(stocks)
        print(f"filtered_latest[{s}]: {n} symbols")
        if not candidate_sector and n > 0:
            candidate_sector = s
            candidate_symbols = [st.get("symbol") for st in stocks if st.get("symbol")]

    if not candidate_sector:
        print("No sector has symbols passing filters. Consider lowering min volume/price.")
        return

    # For candidate sector, check how many symbols have an 'ago' snapshot
    with SessionLocal() as db:
        rows = db.execute(
            text(
                """
                WITH latest AS (
                  SELECT symbol, price,
                         ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY recorded_at DESC) AS rn
                  FROM stock_prices_1d WHERE symbol = ANY(:symbols)
                ),
                ago_before AS (
                  SELECT symbol, price,
                         ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY recorded_at DESC) AS rn
                  FROM stock_prices_1d
                  WHERE symbol = ANY(:symbols) AND recorded_at <= :cutoff
                ),
                ago_after AS (
                  SELECT symbol, price,
                         ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY recorded_at ASC) AS rn
                  FROM stock_prices_1d
                  WHERE symbol = ANY(:symbols) AND recorded_at > :cutoff AND recorded_at <= :cutoff_plus
                )
                SELECT l.symbol,
                       MAX(l.price) FILTER (WHERE l.rn = 1) AS now_price,
                       COALESCE(
                           MAX(ab.price) FILTER (WHERE ab.rn = 1),
                           MAX(aa.price) FILTER (WHERE aa.rn = 1)
                       ) AS ago_price
                FROM latest l
                LEFT JOIN ago_before ab ON ab.symbol = l.symbol
                LEFT JOIN ago_after aa ON aa.symbol = l.symbol
                GROUP BY l.symbol
                """
            ),
            {"symbols": candidate_symbols, "cutoff": cutoff, "cutoff_plus": cutoff_plus},
        ).fetchall()

    has_both = [(sym, float(now or 0.0), float(ago or 0.0)) for sym, now, ago in rows if (now or 0) and (ago or 0)]
    print(f"candidate_sector={candidate_sector}, symbols_with_now_and_ago={len(has_both)} / {len(candidate_symbols)}")
    if has_both:
        preview = has_both[:5]
        print("sample returns (percent):")
        for sym, now_p, ago_p in preview:
            ret = ((now_p - ago_p) / ago_p) * 100.0 if ago_p > 0 else 0.0
            print(f"  {sym}: now={now_p:.4f} ago={ago_p:.4f} ret={ret:.3f}%")
    else:
        print("No symbols with both snapshots within 30m±5m for the candidate sector.")


if __name__ == "__main__":
    main()


