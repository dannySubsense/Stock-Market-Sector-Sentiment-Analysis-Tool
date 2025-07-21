#!/usr/bin/env python3
"""
Test FMP API rate limiting behavior
"""
import asyncio
import time
import httpx
from core.config import get_settings


async def test_fmp_rate_limits():
    """Test FMP API calls to see if we're actually hitting rate limits"""
    print("🧪 Testing FMP API Rate Limits...")
    print("=" * 50)

    settings = get_settings()
    if not settings.credentials or not settings.credentials.api_keys.get("fmp"):
        print("❌ No FMP API key configured")
        return

    api_key = settings.credentials.api_keys["fmp"].key
    print(f"🔑 API Key: {api_key[:10]}...")
    print(f"📊 Configured Tier: {settings.credentials.api_keys['fmp'].tier}")
    print()

    # Test stocks from the failing test
    test_symbols = ["VYX", "ACMR", "KLIC", "PLUS", "CSGS"]

    client = httpx.AsyncClient(timeout=10.0)

    try:
        success_count = 0
        fail_count = 0

        for i, symbol in enumerate(test_symbols, 1):
            print(f"📈 Test {i}/5: Getting quote for {symbol}")

            start_time = time.time()

            try:
                url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
                params = {"apikey": api_key}

                response = await client.get(url, params=params)
                end_time = time.time()

                print(f"   Status: {response.status_code}")
                print(f"   Response time: {(end_time - start_time)*1000:.0f}ms")

                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        price = data[0].get("price", "N/A")
                        print(f"   Price: ${price}")
                        success_count += 1
                    else:
                        print(f"   ⚠️ Empty response")
                        fail_count += 1
                elif response.status_code == 429:
                    print(f"   ❌ RATE LIMITED: {response.text}")
                    fail_count += 1
                else:
                    print(f"   ❌ Error: {response.status_code} - {response.text}")
                    fail_count += 1

            except Exception as e:
                print(f"   ❌ Exception: {e}")
                fail_count += 1

            print()

            # Small delay between calls
            if i < len(test_symbols):
                await asyncio.sleep(0.1)

        print("📊 SUMMARY:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Failed: {fail_count}")
        print(
            f"   📈 Success Rate: {success_count/(success_count+fail_count)*100:.1f}%"
        )

        if fail_count > 0:
            print("\n💡 POSSIBLE ISSUES:")
            print("   1. API key tier might be wrong in config")
            print("   2. There might be daily/monthly limits even on unlimited plans")
            print("   3. Previous tests might have exhausted limits")
            print("   4. API endpoint might have changed")

    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(test_fmp_rate_limits())
