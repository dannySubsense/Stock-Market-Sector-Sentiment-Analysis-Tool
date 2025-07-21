#!/usr/bin/env python3
"""
Test different volume thresholds with NASDAQ+NYSE
Find optimal balance between liquidity and universe size
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.fmp_client import FMPMCPClient


async def test_volume_thresholds():
    """Test different volume thresholds to find optimal universe size"""
    print("📊 Testing Volume Thresholds for Liquidity...")
    print("=" * 60)
    print("📊 Base: NASDAQ+NYSE, Market Cap $10M-$2B")
    print("🎯 Finding optimal volume threshold for sector sentiment")
    print("=" * 60)

    client = FMPMCPClient()

    # Test different volume thresholds
    volume_tests = [
        ("No volume filter", None),
        ("50K daily", 50000),
        ("100K daily", 100000),
        ("250K daily", 250000),
        ("500K daily", 500000),
        ("1M daily (current)", 1000000),
    ]

    results = []

    try:
        for test_name, volume_threshold in volume_tests:
            print(f"\n🧪 Testing: {test_name}")
            print("-" * 40)

            # Build parameters
            url = f"{client.base_url}/v3/stock-screener"
            params = {
                "marketCapMoreThan": "10000000",  # $10M minimum
                "marketCapLowerThan": "2000000000",  # $2B maximum
                "exchange": "NASDAQ,NYSE",  # Both exchanges
                "limit": "10000",  # High limit
                "apikey": client.api_key,
            }

            # Add volume filter if specified
            if volume_threshold:
                params["volumeMoreThan"] = str(volume_threshold)

            print(f"⏳ Calling FMP with volume filter: {volume_threshold or 'None'}...")

            response = await client.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            universe_size = len(data) if isinstance(data, list) else 0

            # Calculate reduction from baseline (no volume filter)
            if volume_threshold is None:
                baseline_size = universe_size
                reduction_pct = 0
            else:
                reduction_pct = (
                    ((baseline_size - universe_size) / baseline_size) * 100
                    if "baseline_size" in locals()
                    else 0
                )

            results.append((test_name, volume_threshold, universe_size, reduction_pct))

            print(f"📊 Result: {universe_size} stocks")
            if volume_threshold:
                print(
                    f"📉 Reduction: -{baseline_size - universe_size} stocks ({reduction_pct:.1f}%)"
                )

            # Show sample for interesting thresholds
            if volume_threshold in [100000, 250000]:
                print(f"\n📋 Sample stocks (first 3):")
                for i, stock in enumerate(data[:3]):
                    symbol = stock.get("symbol", "N/A")
                    name = stock.get("companyName", "N/A")
                    volume = stock.get("volume", "N/A")
                    sector = stock.get("sector", "N/A")

                    print(f"   {i+1}. {symbol} - {name}")
                    print(
                        f"      📊 Volume: {volume:,}"
                        if isinstance(volume, (int, float))
                        else f"      📊 Volume: {volume}"
                    )
                    print(f"      🏭 Sector: {sector}")

        # Summary comparison
        print(f"\n🎯 VOLUME THRESHOLD COMPARISON:")
        print("=" * 60)
        for test_name, volume_threshold, universe_size, reduction_pct in results:
            volume_str = f"{volume_threshold:,}" if volume_threshold else "None"
            print(
                f"   {test_name:20} | {volume_str:>10} | {universe_size:>5} stocks | {reduction_pct:>5.1f}% reduction"
            )

        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   📊 For Maximum Coverage: No volume filter ({results[0][2]} stocks)")
        print(
            f"   ⚖️  For Balanced Approach: 100K-250K threshold (~{[r[2] for r in results if r[1] in [100000, 250000]]}"
        )
        print(f"   🎯 For High Liquidity: 500K+ threshold")
        print(
            f"   ❌ Current 1M threshold too restrictive: only {results[-1][2]} stocks"
        )

    except Exception as e:
        print(f"💥 ERROR: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_volume_thresholds())
