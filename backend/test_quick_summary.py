#!/usr/bin/env python3
"""
Quick Summary Test - Visible Results
Shows performance metrics in a compact format
"""
import asyncio
import time
from collections import defaultdict

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from services.stock_data_retrieval_1d import StockDataRetrieval1D


async def quick_performance_test():
    """Run a quick visible performance test"""
    print("🚀 QUICK PERFORMANCE SUMMARY")
    print("=" * 40)

    # Get universe stats
    session = SessionLocal()
    try:
        all_stocks = (
            session.query(StockUniverse.symbol, StockUniverse.sector)
            .filter(StockUniverse.sector != "unknown")
            .all()
        )

        sectors_data = defaultdict(list)
        for stock in all_stocks:
            sectors_data[stock.sector].append(stock.symbol)
    finally:
        session.close()

    total_stocks = sum(len(symbols) for symbols in sectors_data.values())

    print(f"📊 Universe: {total_stocks} stocks in {len(sectors_data)} sectors")

    # Test with a representative sample
    data_retrieval = StockDataRetrieval1D()
    sample_size = 100

    # Get sample stocks
    sample_symbols = []
    for sector, symbols in sectors_data.items():
        sector_sample = min(10, len(symbols))  # Max 10 per sector
        sample_symbols.extend(symbols[:sector_sample])

    sample_symbols = sample_symbols[:sample_size]

    print(f"🧪 Testing {len(sample_symbols)} sample stocks...")

    # Test with 10 concurrent
    start_time = time.time()
    successful = 0
    failed = 0

    semaphore = asyncio.Semaphore(10)

    async def test_stock(symbol):
        nonlocal successful, failed
        async with semaphore:
            try:
                data = await data_retrieval.get_1d_stock_data(symbol, "polygon")
                if data:
                    successful += 1
                    return True
                else:
                    failed += 1
                    return False
            except:
                failed += 1
                return False

    # Run test
    tasks = [test_stock(symbol) for symbol in sample_symbols]
    await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = time.time() - start_time
    speed = len(sample_symbols) / elapsed * 60

    print(f"✅ Results: {successful}/{len(sample_symbols)} successful")
    print(f"⚡ Speed: {speed:.0f} stocks/minute")
    print(f"⏱️ Time: {elapsed:.2f} seconds")

    # Project full universe
    full_time = total_stocks / speed * 60

    print(f"\n🎯 FULL UNIVERSE PROJECTION:")
    print(f"   • Total stocks: {total_stocks}")
    print(f"   • Estimated time: {full_time:.1f} seconds")
    print(f"   • Success rate: {successful/len(sample_symbols)*100:.1f}%")

    print("\n💡 KEY INSIGHTS:")
    if speed > 5000:
        print("   🔥 EXCELLENT: >5000/min - Ultra-fast processing")
    elif speed > 3000:
        print("   ⚡ GREAT: >3000/min - Very fast processing")
    elif speed > 1000:
        print("   ✅ GOOD: >1000/min - Fast processing")
    else:
        print("   ⚠️ SLOW: <1000/min - May need optimization")

    if successful / len(sample_symbols) > 0.95:
        print("   🎯 HIGH SUCCESS: >95% - API working excellently")
    elif successful / len(sample_symbols) > 0.85:
        print("   ✅ GOOD SUCCESS: >85% - API working well")
    else:
        print("   ⚠️ LOW SUCCESS: <85% - May have API issues")


if __name__ == "__main__":
    asyncio.run(quick_performance_test())
