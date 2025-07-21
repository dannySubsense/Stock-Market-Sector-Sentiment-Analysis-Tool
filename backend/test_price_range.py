#!/usr/bin/env python3
"""
Test tight price range to verify FMP filters are working
"""
import asyncio
from mcp.fmp_client import get_fmp_client


async def test_price_range():
    print("🔍 TESTING TIGHT PRICE RANGE - FILTER VERIFICATION")
    print("=" * 60)

    client = get_fmp_client()

    # Test connection
    connection = await client.test_connection()
    if connection["status"] != "success":
        print(f"❌ Connection failed: {connection['message']}")
        return

    print("✅ FMP Connected")
    print()

    # Test 1: Original range ($1-$100)
    print("🧪 Test 1: Original Price Range ($1.00 - $100.00)")
    result1 = await client.get_stock_screener_complete()
    count1 = result1.get("universe_size", 0)
    print(f"   Result: {count1} stocks")

    if count1 > 0:
        sample_prices = []
        for stock in result1["stocks"][:5]:
            price = stock.get("price", 0)
            symbol = stock.get("symbol", "N/A")
            sample_prices.append(f"{symbol}: ${price:.2f}")
        print(f"   Sample prices: {', '.join(sample_prices)}")
    print()

    # Test 2: Tight range ($1-$10) - should be MUCH smaller
    print("🧪 Test 2: TIGHT Price Range ($1.00 - $10.00)")

    # Manual API call with tight price range
    import httpx
    from core.config import get_settings

    settings = get_settings()
    if not settings.credentials or not settings.credentials.api_keys.get("fmp"):
        print("❌ No FMP API key configured")
        return
    api_key = settings.credentials.api_keys["fmp"].key

    params = {
        "marketCapMoreThan": "10000000",
        "marketCapLowerThan": "2000000000",
        "exchange": "NASDAQ,NYSE",
        "volumeMoreThan": "1000000",
        "priceMoreThan": "1.00",
        "priceLowerThan": "10.00",  # TIGHT RANGE
        "isActivelyTrading": "true",
        "apikey": api_key,
    }

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        response = await http_client.get(
            "https://financialmodelingprep.com/api/v3/stock-screener", params=params
        )

        if response.status_code == 200:
            data = response.json()
            count2 = len(data) if isinstance(data, list) else 0
            print(f"   Result: {count2} stocks")

            if count2 > 0:
                sample_prices = []
                for stock in data[:5]:
                    price = stock.get("price", 0)
                    symbol = stock.get("symbol", "N/A")
                    sample_prices.append(f"{symbol}: ${price:.2f}")
                print(f"   Sample prices: {', '.join(sample_prices)}")

            # Verify price compliance
            if count2 > 0 and isinstance(data, list):
                prices = [
                    stock.get("price", 0) for stock in data if stock.get("price", 0) > 0
                ]
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    print(
                        f"   Price range verification: ${min_price:.2f} - ${max_price:.2f}"
                    )

                    if max_price > 10.00:
                        print(
                            "   ❌ PROBLEM: Prices above $10 found! Filters not working!"
                        )
                    else:
                        print("   ✅ Price filter working correctly")
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")

    print()

    # Test 3: Even tighter ($2-$5)
    print("🧪 Test 3: VERY TIGHT Range ($2.00 - $5.00)")

    params_very_tight = {
        "marketCapMoreThan": "10000000",
        "marketCapLowerThan": "2000000000",
        "exchange": "NASDAQ,NYSE",
        "volumeMoreThan": "1000000",
        "priceMoreThan": "2.00",
        "priceLowerThan": "5.00",  # VERY TIGHT
        "isActivelyTrading": "true",
        "apikey": api_key,
    }

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        response = await http_client.get(
            "https://financialmodelingprep.com/api/v3/stock-screener",
            params=params_very_tight,
        )

        if response.status_code == 200:
            data = response.json()
            count3 = len(data) if isinstance(data, list) else 0
            print(f"   Result: {count3} stocks")

            if count3 > 0:
                sample_prices = []
                for stock in data[:5]:
                    price = stock.get("price", 0)
                    symbol = stock.get("symbol", "N/A")
                    sample_prices.append(f"{symbol}: ${price:.2f}")
                print(f"   Sample prices: {', '.join(sample_prices)}")

    print()
    print("=" * 60)
    print("ANALYSIS:")
    print(f"Original ($1-$100): {count1} stocks")
    print(f"Tight ($1-$10):     {count2 if 'count2' in locals() else 'N/A'} stocks")
    print(f"Very Tight ($2-$5): {count3 if 'count3' in locals() else 'N/A'} stocks")
    print()

    if "count2" in locals() and count1 == count2:
        print("🚨 SUSPICIOUS: Same count despite tighter price range!")
        print("   Possible issues:")
        print("   • FMP filters not being applied")
        print("   • Free tier limitations")
        print("   • API parameter issues")
    elif "count2" in locals() and count2 < count1:
        print("✅ GOOD: Filters are working - count decreased as expected")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_price_range())
