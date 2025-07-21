#!/usr/bin/env python3
"""
FMP Filter Testing Script
Test different filter combinations to understand universe size limitations
"""
import asyncio
import httpx
from typing import Dict, Any


class FMPFilterTester:
    """Test different FMP filter combinations"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/api/v3/stock-screener"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_filters(
        self, filters: Dict[str, str], description: str
    ) -> Dict[str, Any]:
        """Test a specific filter combination"""
        try:
            params = {**filters, "apikey": self.api_key}

            print(f"🧪 Testing: {description}")
            print(f"   Filters: {filters}")

            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()

            data = response.json()
            count = len(data) if isinstance(data, list) else 0

            print(f"   ✅ Result: {count} stocks")

            # Show sample symbols if we got results
            if count > 0 and isinstance(data, list):
                symbols = [stock.get("symbol", "N/A") for stock in data[:5]]
                print(f"   Sample: {', '.join(symbols)}")

            print()
            return {
                "status": "success",
                "count": count,
                "data": data[:3] if count > 0 else [],
            }

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            print()
            return {"status": "error", "count": 0, "error": str(e)}

    async def close(self):
        await self.client.aclose()


async def run_filter_tests():
    """Run comprehensive filter tests"""
    print("🔬 FMP FILTER TESTING - UNIVERSE SIZE VALIDATION")
    print("=" * 80)
    print()

    # Get API key (same way as FMP client)
    from core.config import get_settings

    settings = get_settings()

    if not settings.credentials or not settings.credentials.api_keys.get("fmp"):
        print("❌ No FMP API key configured")
        return

    api_key = settings.credentials.api_keys["fmp"].key
    tester = FMPFilterTester(api_key)

    try:
        # Test 1: Original strict criteria
        await tester.test_filters(
            {
                "marketCapMoreThan": "10000000",  # $10M
                "marketCapLowerThan": "2000000000",  # $2B
                "exchange": "NASDAQ,NYSE",
                "volumeMoreThan": "1000000",  # 1M volume - RESTRICTIVE
                "priceMoreThan": "1.00",
                "priceLowerThan": "100.00",
                "isActivelyTrading": "true",
            },
            "Original Criteria (Current: 492 stocks)",
        )

        # Test 2: Lower volume threshold
        await tester.test_filters(
            {
                "marketCapMoreThan": "10000000",
                "marketCapLowerThan": "2000000000",
                "exchange": "NASDAQ,NYSE",
                "volumeMoreThan": "500000",  # 500K volume - LESS RESTRICTIVE
                "priceMoreThan": "1.00",
                "priceLowerThan": "100.00",
                "isActivelyTrading": "true",
            },
            "Lower Volume Threshold (500K+)",
        )

        # Test 3: Much lower volume threshold
        await tester.test_filters(
            {
                "marketCapMoreThan": "10000000",
                "marketCapLowerThan": "2000000000",
                "exchange": "NASDAQ,NYSE",
                "volumeMoreThan": "100000",  # 100K volume - MUCH LESS RESTRICTIVE
                "priceMoreThan": "1.00",
                "priceLowerThan": "100.00",
                "isActivelyTrading": "true",
            },
            "Much Lower Volume (100K+)",
        )

        # Test 4: No volume filter
        await tester.test_filters(
            {
                "marketCapMoreThan": "10000000",
                "marketCapLowerThan": "2000000000",
                "exchange": "NASDAQ,NYSE",
                # NO VOLUME FILTER
                "priceMoreThan": "1.00",
                "priceLowerThan": "100.00",
                "isActivelyTrading": "true",
            },
            "No Volume Filter",
        )

        # Test 5: Market cap only
        await tester.test_filters(
            {
                "marketCapMoreThan": "10000000",
                "marketCapLowerThan": "2000000000",
                "exchange": "NASDAQ,NYSE",
                "isActivelyTrading": "true",
                # NO VOLUME OR PRICE FILTERS
            },
            "Market Cap + Exchange Only",
        )

        # Test 6: Just exchange filter
        await tester.test_filters(
            {
                "exchange": "NASDAQ,NYSE",
                "isActivelyTrading": "true",
                # MINIMAL FILTERS
            },
            "Exchange + Active Only (Total Universe)",
        )

        # Test 7: Alternative volume (250K)
        await tester.test_filters(
            {
                "marketCapMoreThan": "10000000",
                "marketCapLowerThan": "2000000000",
                "exchange": "NASDAQ,NYSE",
                "volumeMoreThan": "250000",  # 250K volume
                "priceMoreThan": "1.00",
                "priceLowerThan": "100.00",
                "isActivelyTrading": "true",
            },
            "Alternative Volume (250K+)",
        )

        # Test 8: Higher market cap minimum
        await tester.test_filters(
            {
                "marketCapMoreThan": "50000000",  # $50M instead of $10M
                "marketCapLowerThan": "2000000000",
                "exchange": "NASDAQ,NYSE",
                "volumeMoreThan": "1000000",
                "priceMoreThan": "1.00",
                "priceLowerThan": "100.00",
                "isActivelyTrading": "true",
            },
            "Higher Market Cap Min ($50M+)",
        )

    finally:
        await tester.close()

    print("=" * 80)
    print("ANALYSIS:")
    print(
        "• If volume threshold significantly affects count → Volume is the limiting factor"
    )
    print(
        "• If market cap only gives much higher count → Price/volume filters are restrictive"
    )
    print("• If total universe is reasonable → Our filtering is appropriate")
    print("• Compare with known small-cap indices (Russell 2000 has ~2,000 stocks)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_filter_tests())
