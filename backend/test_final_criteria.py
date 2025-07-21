#!/usr/bin/env python3
"""
Test our final optimized universe criteria
Should return ~2780 stocks with 100K volume minimum
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.fmp_client import FMPMCPClient


async def test_final_criteria():
    """Test our updated get_stock_screener_complete with optimized criteria"""
    print("🎯 Testing Final Optimized Universe Criteria...")
    print("=" * 60)
    print("📊 NEW Criteria:")
    print("   • Market Cap: $10M - $2B")
    print("   • Volume: 100K+ daily (liquidity optimized)")
    print("   • Exchanges: NASDAQ, NYSE")
    print("   • No price restrictions")
    print("   • Expected: ~2780 stocks")
    print("=" * 60)

    client = FMPMCPClient()

    try:
        # Use our updated method
        result = await client.get_stock_screener_complete()

        if result["status"] == "success":
            universe_size = result["universe_size"]
            stocks = result["stocks"]
            criteria = result["criteria"]

            print(f"\n📊 RESULTS:")
            print(f"   🎯 Universe Size: {universe_size} stocks")
            print(
                f"   📈 vs Expected (~2780): {'✅ Match!' if 2700 <= universe_size <= 2850 else '❌ Different'}"
            )
            print(
                f"   📈 vs Old Restrictive (492): +{universe_size - 492} stocks ({((universe_size - 492) / 492 * 100):.0f}% increase)"
            )

            print(f"\n📋 Applied Criteria:")
            for key, value in criteria.items():
                print(f"   • {key.replace('_', ' ').title()}: {value}")

            if stocks:
                print(f"\n📋 Sample stocks (first 5):")
                for i, stock in enumerate(stocks[:5]):
                    symbol = stock.get("symbol", "N/A")
                    name = stock.get("companyName", "N/A")
                    market_cap = stock.get("marketCap", "N/A")
                    volume = stock.get("volume", "N/A")
                    sector = stock.get("sector", "N/A")
                    price = stock.get("price", "N/A")

                    print(f"   {i+1}. {symbol} - {name}")
                    print(
                        f"      💰 Market Cap: ${market_cap:,}"
                        if isinstance(market_cap, (int, float))
                        else f"      💰 Market Cap: {market_cap}"
                    )
                    print(
                        f"      📊 Volume: {volume:,}"
                        if isinstance(volume, (int, float))
                        else f"      📊 Volume: {volume}"
                    )
                    print(f"      💲 Price: ${price}")
                    print(f"      🏭 Sector: {sector}")
                    print()

                # Quick sector distribution
                sectors = {}
                for stock in stocks:
                    sector = stock.get("sector", "Unknown")
                    sectors[sector] = sectors.get(sector, 0) + 1

                print(f"🏭 Top 5 Sectors:")
                for sector, count in sorted(
                    sectors.items(), key=lambda x: x[1], reverse=True
                )[:5]:
                    pct = (count / universe_size) * 100
                    print(f"   {sector}: {count} stocks ({pct:.1f}%)")

                print(f"\n✅ SUCCESS: Universe ready for sector sentiment analysis!")
                print(f"📊 Final Universe: {universe_size} liquid small-cap stocks")

        else:
            print(f"❌ ERROR: {result.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_final_criteria())
