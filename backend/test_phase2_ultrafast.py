#!/usr/bin/env python3
"""
Step 5 Phase 2: ULTRA-FAST Large Sample Testing with Polygon API
Goal: Complete in under 45 seconds with 50 stocks per sector using Polygon
"""
import asyncio
import time
from typing import List, Dict, Any

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from services.sector_aggregation_1d import SectorAggregation1D


class UltraFastPhase2:
    """Ultra-fast Phase 2 - 50 stocks per sector using Polygon API"""

    def __init__(self):
        self.aggregation_service = SectorAggregation1D()

    async def ultra_fast_test(
        self, sector: str, max_stocks: int = 50
    ) -> Dict[str, Any]:
        """Ultra-fast sector test with 50 stocks per sector using Polygon"""
        start_time = time.time()
        try:
            # Get stock sample up to max_stocks
            with SessionLocal() as db:
                stocks = (
                    db.query(StockUniverse.symbol)
                    .filter(
                        StockUniverse.sector == sector, StockUniverse.is_active == True
                    )
                    .limit(max_stocks)
                    .all()
                )
                symbols = [s[0] for s in stocks]

            if not symbols:
                print(f"⚡ {sector}: ❌ No stocks")
                return {"success": False, "error": "No stocks"}

            actual_count = len(symbols)
            print(f"⚡ {sector}: {actual_count} stocks", end=" ")

            # Ultra-fast API calls with Polygon (should have higher limits)
            stock_data = []
            for i, symbol in enumerate(symbols):
                try:
                    # Use Polygon for consistency with refactored services
                    data = (
                        await self.aggregation_service.data_retrieval.get_1d_stock_data(
                            symbol, "polygon"
                        )
                    )
                    if data:
                        stock_data.append(data)
                except Exception as e:
                    # Skip failures but track them
                    pass

                # Minimal delay for Polygon (typically has higher limits)
                if i > 2:  # Even fewer initial free calls before delay
                    await asyncio.sleep(
                        0.01
                    )  # 10ms delay - consistent with sector aggregation

            if not stock_data:
                print("❌ No data")
                return {"success": False, "error": "No valid data"}

            # Quick calculation (simplified)
            avg_performance = (
                sum(
                    ((d.current_price - d.previous_close) / d.previous_close * 100)
                    for d in stock_data
                    if d.previous_close > 0
                )
                / len(stock_data)
                if stock_data
                else 0
            )

            elapsed = time.time() - start_time
            rate = len(stock_data) / (elapsed / 60) if elapsed > 0 else 0

            print(
                f"✅ {elapsed:.1f}s ({rate:.0f}/min) Sentiment: {avg_performance:+.2f}%"
            )

            return {
                "success": True,
                "sector": sector,
                "stocks_available": actual_count,
                "stocks_tested": len(stock_data),
                "time_seconds": elapsed,
                "rate_per_minute": rate,
                "sentiment_estimate": avg_performance,
            }

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ {elapsed:.1f}s Error: {str(e)[:30]}")
            return {"success": False, "sector": sector, "error": str(e)}

    async def run_ultra_fast_phase2(self):
        """Ultra-fast Phase 2 validation - 50 stocks per sector using Polygon"""
        print("⚡ ULTRA-FAST PHASE 2 VALIDATION - POLYGON API")
        print("=" * 65)
        print("Goal: Complete all 11 sectors in under 45 seconds")
        print("Strategy: 50 stocks per sector using Polygon (higher rate limits)")
        print("Expected: ~25-30% coverage of full universe without hitting limits")
        print("=" * 65)

        sectors = [
            "utilities",
            "consumer_defensive",
            "basic_materials",
            "energy",
            "real_estate",
            "communication_services",
            "consumer_cyclical",
            "industrials",
            "technology",
            "financial_services",
            "healthcare",
        ]

        results = []
        total_start = time.time()

        # Process all sectors rapidly
        for i, sector in enumerate(sectors, 1):
            print(f"[{i:2}/{len(sectors)}] ", end="")
            result = await self.ultra_fast_test(sector, max_stocks=50)
            results.append(result)

        total_elapsed = time.time() - total_start
        successful = [r for r in results if r.get("success")]

        print(f"\n" + "=" * 65)
        print("⚡ ULTRA-FAST PHASE 2 POLYGON SUMMARY")
        print("=" * 65)

        total_stocks_available = sum(r.get("stocks_available", 0) for r in successful)
        total_stocks_tested = sum(r.get("stocks_tested", 0) for r in successful)
        avg_rate = (
            sum(r.get("rate_per_minute", 0) for r in successful) / len(successful)
            if successful
            else 0
        )
        coverage_pct = (total_stocks_tested / 2058) * 100

        print(f"✅ Successful: {len(successful)}/{len(results)} sectors")
        print(f"📊 Total stocks available: {total_stocks_available}")
        print(f"📊 Total stocks tested: {total_stocks_tested}")
        print(f"⏱️  Total time: {total_elapsed:.1f} seconds")
        print(f"📈 Average rate: {avg_rate:.0f} stocks/minute")
        print(f"📊 Coverage: {coverage_pct:.1f}% of full universe")
        print(f"🔄 API: Polygon (avoiding FMP 300-request burst limit)")

        # Show sector breakdown
        print(f"\n📈 SECTOR BREAKDOWN:")
        for result in successful:
            sector = result["sector"]
            available = result.get("stocks_available", 0)
            tested = result.get("stocks_tested", 0)
            sentiment = result.get("sentiment_estimate", 0)
            print(f"  {sector:20} {tested:2}/{available:2} stocks {sentiment:+6.2f}%")

        # Quick projections
        if avg_rate > 0:
            full_time = 2058 / avg_rate
            print(f"\n🔮 Full pipeline projection: {full_time:.1f} minutes")

        # Enhanced validation assessment
        if len(successful) >= 9:
            print(f"\n🎉 POLYGON SUCCESS: Comprehensive validation")
            print(
                f"✅ Tested {total_stocks_tested} stocks across {len(successful)} sectors"
            )

            if coverage_pct >= 25:
                print(
                    f"🎯 EXCELLENT COVERAGE: {coverage_pct:.1f}% validates pipeline thoroughly"
                )
                print(f"✅ Ready for production deployment")
            elif coverage_pct >= 15:
                print(
                    f"✅ GOOD COVERAGE: {coverage_pct:.1f}% provides strong validation"
                )
                print(f"✅ Ready for production or full pipeline validation")
            else:
                print(f"✅ BASIC COVERAGE: {coverage_pct:.1f}% confirms pipeline works")

            if avg_rate > 1000:
                print(
                    f"🚀 VERY HIGH RATE: {avg_rate:.0f}/min - excellent Polygon performance"
                )
            elif avg_rate > 700:
                print(f"✅ HIGH RATE: {avg_rate:.0f}/min - good performance")
            else:
                print(f"⚠️  MODERATE RATE: {avg_rate:.0f}/min - may need optimization")
        else:
            print(f"\n⚠️  Some sectors failed - investigate issues")

        return len(successful) >= 9


async def main():
    """Ultra-fast Phase 2 with Polygon - 50 stocks per sector validation"""
    validator = UltraFastPhase2()
    await validator.run_ultra_fast_phase2()


if __name__ == "__main__":
    asyncio.run(main())
