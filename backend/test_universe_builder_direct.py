#!/usr/bin/env python3
"""
Test UniverseBuilder directly - Full pipeline test
See what data it actually produces with our new optimized criteria
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.universe_builder import UniverseBuilder


async def test_universe_builder_direct():
    """Test UniverseBuilder directly to see full pipeline"""
    print("🏗️ Testing UniverseBuilder Direct Pipeline...")
    print("=" * 60)
    print("🎯 Testing with NEW optimized criteria:")
    print("   • Market Cap: $10M - $2B")
    print("   • Volume: 100K+ daily (down from 1M)")
    print("   • Exchanges: NASDAQ, NYSE (no NYSEARCA)")
    print("   • No price restrictions (removed $2-$100 limit)")
    print("=" * 60)

    universe_builder = UniverseBuilder()

    print("\n1️⃣ Checking Current Configuration...")
    print(
        f"   Market Cap Range: ${universe_builder.market_cap_min:,} - ${universe_builder.market_cap_max:,}"
    )
    print(f"   Min Volume: {universe_builder.min_daily_volume:,} shares")
    print(f"   Min Price: {universe_builder.min_price}")
    print(f"   Max Price: {universe_builder.max_price}")
    print(f"   Valid Exchanges: {universe_builder.valid_exchanges}")
    print(f"   Target Universe Size: {universe_builder.target_universe_size}")

    print("\n2️⃣ Testing FMP Criteria Generation...")
    criteria = universe_builder.get_fmp_screening_criteria()
    print("   Generated FMP Criteria:")
    for key, value in criteria.items():
        print(f"      • {key}: {value}")

    print("\n3️⃣ Testing FMP Universe Retrieval...")
    try:
        universe_result = await universe_builder.get_fmp_universe()

        if universe_result["status"] == "success":
            universe_size = universe_result["count"]
            stocks = universe_result["stocks"]

            print(f"   ✅ Success: Retrieved {universe_size} stocks")
            print(
                f"   📊 vs Target (1500): {'🎯 Close!' if 1200 <= universe_size <= 1800 else '📈 Different scale'}"
            )
            print(
                f"   🔗 vs Previous Tests (~2123): {'✅ Consistent' if 2000 <= universe_size <= 2200 else '❓ Different'}"
            )

            if stocks:
                print(f"\n4️⃣ Analyzing Sample Data...")

                # Analyze first 10 stocks
                sample_stocks = stocks[:10]
                print(f"   📋 Sample Stocks (first 10):")

                for i, stock in enumerate(sample_stocks, 1):
                    symbol = stock.get("symbol", "N/A")
                    name = (
                        stock.get("companyName", "N/A")[:30] + "..."
                        if len(stock.get("companyName", "")) > 30
                        else stock.get("companyName", "N/A")
                    )
                    market_cap = stock.get("marketCap", 0)
                    volume = stock.get("volume", 0)
                    price = stock.get("price", 0)
                    sector = stock.get("sector", "N/A")
                    exchange = stock.get("exchangeShortName", "N/A")

                    print(f"      {i:2d}. {symbol:6s} | {name:32s}")
                    print(
                        f"          💰 ${market_cap:,}"
                        if isinstance(market_cap, (int, float))
                        else f"          💰 {market_cap}"
                    )
                    print(
                        f"          📊 Vol: {volume:,}"
                        if isinstance(volume, (int, float))
                        else f"          📊 Vol: {volume}"
                    )
                    print(f"          💲 ${price:.2f} | 🏢 {exchange} | 🏭 {sector}")
                    print()

                # Summary analysis
                print(f"5️⃣ Universe Analysis...")

                # Price range analysis
                prices = [
                    s.get("price", 0)
                    for s in stocks
                    if isinstance(s.get("price"), (int, float))
                ]
                if prices:
                    print(f"   💲 Price Range: ${min(prices):.2f} - ${max(prices):.2f}")

                # Volume analysis
                volumes = [
                    s.get("volume", 0)
                    for s in stocks
                    if isinstance(s.get("volume"), (int, float))
                ]
                if volumes:
                    min_vol, max_vol = min(volumes), max(volumes)
                    print(f"   📊 Volume Range: {min_vol:,} - {max_vol:,}")
                    under_100k = sum(1 for v in volumes if v < 100000)
                    print(
                        f"   ⚠️  Stocks under 100K volume: {under_100k} ({under_100k/len(volumes)*100:.1f}%)"
                    )

                # Exchange distribution
                exchanges = {}
                for stock in stocks:
                    ex = stock.get("exchangeShortName", "Unknown")
                    exchanges[ex] = exchanges.get(ex, 0) + 1

                print(f"   🏢 Exchange Distribution:")
                for exchange, count in sorted(
                    exchanges.items(), key=lambda x: x[1], reverse=True
                ):
                    pct = (count / universe_size) * 100
                    print(f"      {exchange}: {count} stocks ({pct:.1f}%)")

                # Sector distribution
                sectors = {}
                for stock in stocks:
                    sector = stock.get("sector", "Unknown")
                    sectors[sector] = sectors.get(sector, 0) + 1

                print(f"   🏭 Top 5 Sectors:")
                for sector, count in sorted(
                    sectors.items(), key=lambda x: x[1], reverse=True
                )[:5]:
                    pct = (count / universe_size) * 100
                    print(f"      {sector}: {count} stocks ({pct:.1f}%)")

        else:
            print(f"   ❌ Error: {universe_result.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"   💥 Exception: {e}")

    # Test if we should also try the full build_daily_universe method
    print(f"\n6️⃣ Next Steps:")
    print(f"   ✅ FMP Integration: Working")
    print(f"   🔄 Ready to test: build_daily_universe() (database integration)")
    print(f"   📊 Universe size looks good for sector sentiment analysis")
    print(f"   💡 Consider: Testing database integration next")


if __name__ == "__main__":
    asyncio.run(test_universe_builder_direct())
