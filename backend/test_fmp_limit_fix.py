#!/usr/bin/env python3
"""
Test script to verify FMP limit parameter fix
Should now return more than 1000 stocks with limit=5000
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.fmp_client import FMPMCPClient


async def test_fmp_limit_fix():
    """Test that we now get more than 1000 stocks with the limit fix"""
    print("🔧 Testing FMP Limit Fix...")
    print("=" * 50)

    client = FMPMCPClient()

    try:
        # Get complete universe with our fixed method
        result = await client.get_stock_screener_complete()

        if result["status"] == "success":
            universe_size = result["universe_size"]
            stocks = result["stocks"]

            print(f"📊 UNIVERSE SIZE: {universe_size} stocks")
            print(f"🎯 Expected: >1000 stocks (previous was exactly 1000)")

            if universe_size > 1000:
                print("✅ SUCCESS: Limit fix worked! Got more than 1000 stocks")
                print(f"🚀 Improvement: +{universe_size - 1000} additional stocks")
            elif universe_size == 1000:
                print("❌ STILL HITTING LIMIT: Still exactly 1000 stocks")
                print("💡 Possible issues:")
                print("   - FMP free tier has 1000 stock limit")
                print("   - API parameter not working as expected")
                print("   - Need different API endpoint")
            else:
                print(f"📉 FEWER THAN BEFORE: Only {universe_size} stocks")

            # Show sample of stock data
            if stocks and len(stocks) > 0:
                print(f"\n📋 Sample stocks (first 3):")
                for i, stock in enumerate(stocks[:3]):
                    symbol = stock.get("symbol", "N/A")
                    name = stock.get("companyName", "N/A")
                    market_cap = stock.get("marketCap", "N/A")
                    sector = stock.get("sector", "N/A")
                    print(f"   {i+1}. {symbol} - {name}")
                    print(f"      Market Cap: {market_cap}, Sector: {sector}")

        else:
            print(f"❌ ERROR: {result.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_fmp_limit_fix())
