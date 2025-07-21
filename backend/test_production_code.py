#!/usr/bin/env python3
"""
Test Production Code: UniverseBuilder.get_fmp_universe()
Runs the actual production method to see real small-cap data
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.universe_builder import UniverseBuilder


async def test_production_universe_builder():
    """Run the actual production UniverseBuilder.get_fmp_universe() method"""
    print("🏭 TESTING ACTUAL PRODUCTION CODE")
    print("=" * 60)
    print("🎯 Method: UniverseBuilder.get_fmp_universe()")
    print("🎯 Expected: Small-cap stocks ($10M-$2B market cap)")
    print("=" * 60)
    print()

    # Create real UniverseBuilder instance
    universe_builder = UniverseBuilder()

    print("📋 PRODUCTION CRITERIA:")
    print(
        f"   Market Cap: ${universe_builder.market_cap_min:,} - ${universe_builder.market_cap_max:,}"
    )
    print(f"   Min Volume: {universe_builder.min_daily_volume:,} shares")
    print(f"   Exchanges: {universe_builder.valid_exchanges}")
    print(
        f"   Price Limits: {universe_builder.min_price} - {universe_builder.max_price}"
    )
    print()

    # Get the actual FMP criteria
    criteria = universe_builder.get_fmp_screening_criteria()
    print("🔧 FMP API PARAMETERS:")
    for key, value in criteria.items():
        print(f"   {key}: {value}")
    print()

    # Run the actual production method
    print("🚀 RUNNING PRODUCTION METHOD...")
    result = await universe_builder.get_fmp_universe()

    if result["status"] == "success":
        universe_size = result["universe_size"]
        stocks = result["stocks"]

        print(f"✅ SUCCESS: Retrieved {universe_size} stocks")
        print()

        if stocks:
            print("📊 SAMPLE SMALL-CAP STOCKS (First 10):")
            print("-" * 80)

            for i, stock in enumerate(stocks[:10], 1):
                symbol = stock.get("symbol", "N/A")
                name = stock.get("companyName", "N/A")[:40]
                market_cap = stock.get("marketCap", 0)
                price = stock.get("price", 0)
                volume = stock.get("volume", 0)
                original_sector = stock.get("original_fmp_sector", "N/A")
                mapped_sector = stock.get("sector", "N/A")

                print(f"{i:2d}. {symbol:6s} | {name:40s}")
                print(
                    f"    💰 Market Cap: ${market_cap:,}"
                    if isinstance(market_cap, (int, float))
                    else f"    💰 Market Cap: {market_cap}"
                )
                print(
                    f"    💲 Price: ${price:.2f}"
                    if isinstance(price, (int, float))
                    else f"    💲 Price: {price}"
                )
                print(
                    f"    📊 Volume: {volume:,}"
                    if isinstance(volume, (int, float))
                    else f"    📊 Volume: {volume}"
                )
                print(f"    🏭 FMP Sector: {original_sector}")
                print(f"    🎯 Mapped Sector: {mapped_sector}")
                print()

            # Validate these are actually small-caps
            print("🔍 SMALL-CAP VALIDATION:")
            small_cap_count = 0
            large_cap_count = 0

            for stock in stocks[:50]:  # Check first 50
                market_cap = stock.get("marketCap", 0)
                if isinstance(market_cap, (int, float)):
                    if 10_000_000 <= market_cap <= 2_000_000_000:
                        small_cap_count += 1
                    else:
                        large_cap_count += 1

            print(
                f"   ✅ Small-cap stocks (${10_000_000:,} - ${2_000_000_000:,}): {small_cap_count}"
            )
            print(f"   ❌ Outside range: {large_cap_count}")

            if small_cap_count > large_cap_count:
                print("   🎯 SUCCESS: Mostly small-cap stocks as expected!")
            else:
                print("   ⚠️  WARNING: Many stocks outside small-cap range")

    else:
        print(f"❌ ERROR: {result.get('message', 'Unknown error')}")

    print()
    print("🏁 PRODUCTION CODE TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(test_production_universe_builder())
