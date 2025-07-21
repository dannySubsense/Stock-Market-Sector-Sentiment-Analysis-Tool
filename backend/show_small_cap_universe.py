#!/usr/bin/env python3
"""
Show Small-Cap Universe by Sectors
Simple script to display production small-cap universe organized by sectors
"""
import asyncio
import sys
import os
from collections import defaultdict

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.universe_builder import UniverseBuilder


async def show_small_cap_universe():
    """Show small-cap universe organized by sectors"""
    print("📊 SMALL-CAP UNIVERSE BY SECTORS")
    print("=" * 60)

    # Get universe from production code
    universe_builder = UniverseBuilder()
    result = await universe_builder.get_fmp_universe()

    if result["status"] != "success":
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
        return

    stocks = result["stocks"]
    print(f"Total Stocks: {len(stocks)}")
    print()

    # Organize by sector
    sectors = defaultdict(list)
    for stock in stocks:
        sector = stock.get("sector", "unknown_sector")
        sectors[sector].append(stock)

    # Show each sector
    for sector_name, sector_stocks in sorted(sectors.items()):
        print(
            f"🏭 {sector_name.upper().replace('_', ' ')} ({len(sector_stocks)} stocks)"
        )
        print("-" * 50)

        # Show first 5 stocks in each sector
        for i, stock in enumerate(sector_stocks[:5], 1):
            symbol = stock.get("symbol", "N/A")
            name = stock.get("companyName", "N/A")[:35]
            market_cap = stock.get("marketCap", 0)
            price = stock.get("price", 0)

            print(f"  {i}. {symbol:6s} | {name:35s} | ${market_cap:,} | ${price:.2f}")

        if len(sector_stocks) > 5:
            print(f"     ... and {len(sector_stocks) - 5} more stocks")
        print()


if __name__ == "__main__":
    asyncio.run(show_small_cap_universe())
