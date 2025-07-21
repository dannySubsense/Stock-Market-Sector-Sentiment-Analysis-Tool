#!/usr/bin/env python3
"""
Test FMP screener with ONLY market cap filter
No price, volume, exchange restrictions - just $10M-$2B market cap
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.fmp_client import FMPMCPClient


async def test_market_cap_only():
    """Test FMP screener with only market cap filter"""
    print("🏢 Testing Market Cap Only Filter...")
    print("=" * 60)
    print("📊 Criteria: Market Cap $10M - $2B ONLY")
    print("🚫 NO price, volume, or exchange filters")
    print("=" * 60)

    client = FMPMCPClient()

    try:
        # Manual call with only market cap filter
        url = f"{client.base_url}/v3/stock-screener"
        params = {
            "marketCapMoreThan": "10000000",  # $10M minimum
            "marketCapLowerThan": "2000000000",  # $2B maximum
            "limit": "5000",  # Maximum limit
            "apikey": client.api_key,
            # NO OTHER FILTERS - just market cap
        }

        print(f"🔗 URL: {url}")
        print(f"📋 Params: {params}")
        print("\n⏳ Calling FMP API...")

        response = await client.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        universe_size = len(data) if isinstance(data, list) else 0

        print(f"\n📊 RESULTS:")
        print(f"   🎯 Universe Size: {universe_size} stocks")
        print(f"   📈 vs Current (492): +{universe_size - 492} additional stocks")
        print(
            f"   🎪 vs Target (1,200-1,500): {'✅ Within range' if 1200 <= universe_size <= 1500 else '❌ Outside range'}"
        )

        if universe_size > 0:
            # Show sample data
            print(f"\n📋 Sample stocks (first 5):")
            for i, stock in enumerate(data[:5]):
                symbol = stock.get("symbol", "N/A")
                name = stock.get("companyName", "N/A")
                market_cap = stock.get("marketCap", "N/A")
                price = stock.get("price", "N/A")
                volume = stock.get("volume", "N/A")
                exchange = stock.get("exchangeShortName", "N/A")
                sector = stock.get("sector", "N/A")

                print(f"   {i+1}. {symbol} - {name}")
                print(
                    f"      💰 Market Cap: ${market_cap:,}"
                    if isinstance(market_cap, (int, float))
                    else f"      💰 Market Cap: {market_cap}"
                )
                print(
                    f"      💲 Price: ${price}, 📊 Volume: {volume}, 🏢 Exchange: {exchange}"
                )
                print(f"      🏭 Sector: {sector}")
                print()

            # Analyze what we're losing with current filters
            print(f"\n🔍 FILTER IMPACT ANALYSIS:")
            print(f"   📊 Market Cap Only: {universe_size} stocks")
            print(f"   🎯 With All Filters: 492 stocks")
            print(
                f"   📉 Lost to Filters: {universe_size - 492} stocks ({((universe_size - 492) / universe_size * 100):.1f}%)"
            )

        else:
            print("❌ No data returned")

    except Exception as e:
        print(f"💥 ERROR: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_market_cap_only())
