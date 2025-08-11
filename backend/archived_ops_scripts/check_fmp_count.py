#!/usr/bin/env python3
"""
Quick diagnostic to check FMP universe count
"""
import asyncio
from mcp.fmp_client import get_fmp_client


async def check_universe_count():
    print("🔍 DIAGNOSTIC: Checking FMP Universe Count")
    print("=" * 50)

    client = get_fmp_client()

    # Test connection
    connection = await client.test_connection()
    print(f"Connection: {connection['status']}")

    if connection["status"] != "success":
        print(f"❌ Connection failed: {connection['message']}")
        return

    # Get universe
    result = await client.get_stock_screener_complete()

    print(f"API Status: {result['status']}")
    print(f"Universe Size: {result.get('universe_size', 0)}")
    print(f"Stocks Array Length: {len(result.get('stocks', []))}")

    if result["status"] == "success":
        stocks = result["stocks"]
        print(f"\nFirst 5 stock symbols:")
        for i, stock in enumerate(stocks[:5]):
            print(f"  {i+1}. {stock.get('symbol', 'NO_SYMBOL')}")

        if len(stocks) > 5:
            print(f"  ... and {len(stocks) - 5} more")
    else:
        print(f"❌ Error: {result.get('message', 'Unknown error')}")

    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(check_universe_count())
