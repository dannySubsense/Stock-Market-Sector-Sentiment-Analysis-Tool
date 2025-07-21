#!/usr/bin/env python3
"""
Test FMP screener with AMEX only + higher limits
Find the TRUE AMEX universe size without hitting API limits
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.fmp_client import FMPMCPClient


async def test_amex_with_limits():
    """Test different limit values with AMEX only"""
    print("🇺🇸 Testing AMEX Universe with Higher Limits...")
    print("=" * 60)
    print("📊 Criteria: Market Cap $10M-$2B, AMEX only")
    print("🎯 Testing multiple limit values to find true size")
    print("=" * 60)

    client = FMPMCPClient()

    # Test different limit values
    test_limits = [1000, 2000, 5000, 10000]

    try:
        for limit in test_limits:
            print(f"\n🧪 Testing limit: {limit}")
            print("-" * 40)

            # Manual call with AMEX only
            url = f"{client.base_url}/v3/stock-screener"
            params = {
                "marketCapMoreThan": "10000000",  # $10M minimum
                "marketCapLowerThan": "2000000000",  # $2B maximum
                "exchange": "AMEX",  # AMEX only
                "limit": str(limit),
                "apikey": client.api_key,
            }

            print(f"⏳ Calling FMP with limit={limit}...")

            response = await client.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            universe_size = len(data) if isinstance(data, list) else 0

            print(f"📊 Result: {universe_size} stocks")

            # Check if we hit the limit
            if universe_size == limit:
                print(f"⚠️  HITTING LIMIT! (exactly {limit})")
            elif universe_size < limit:
                print(f"✅ FOUND TRUE SIZE! ({universe_size} < {limit})")

                # Show some sample data for the final result
                print(f"\n📋 Sample AMEX stocks (first 5):")
                for i, stock in enumerate(data[:5] if data else []):
                    symbol = stock.get("symbol", "N/A")
                    name = stock.get("companyName", "N/A")
                    market_cap = stock.get("marketCap", "N/A")
                    sector = stock.get("sector", "N/A")

                    print(f"   {i+1}. {symbol} - {name}")
                    print(
                        f"      💰 Market Cap: ${market_cap:,}"
                        if isinstance(market_cap, (int, float))
                        else f"      💰 Market Cap: {market_cap}"
                    )
                    print(f"      🏭 Sector: {sector}")

                print(f"\n🎯 AMEX Universe Summary:")
                print(f"   📊 Total AMEX stocks ($10M-$2B): {universe_size}")
                print(f"   📈 vs NASDAQ (6243): -{6243 - universe_size} stocks")
                print(
                    f"   📈 vs NYSE (1533): {'+' if universe_size > 1533 else '-'}{abs(universe_size - 1533)} stocks"
                )
                print(
                    f"   🏢 Combined ALL EXCHANGES estimate: ~{universe_size + 6243 + 1533} stocks"
                )

                # Count by sector if we have data
                if data and universe_size > 0:
                    sectors = {}
                    for stock in data:
                        sector = stock.get("sector", "Unknown")
                        sectors[sector] = sectors.get(sector, 0) + 1

                    print(f"\n🏭 AMEX Sector Distribution:")
                    for sector, count in sorted(
                        sectors.items(), key=lambda x: x[1], reverse=True
                    ):
                        pct = (count / universe_size) * 100
                        print(f"   {sector}: {count} stocks ({pct:.1f}%)")
                else:
                    print(
                        f"\n📝 AMEX appears to be a smaller exchange for small-cap universe"
                    )

                break
            else:
                print(f"🔄 Continue testing...")

    except Exception as e:
        print(f"💥 ERROR: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_amex_with_limits())
