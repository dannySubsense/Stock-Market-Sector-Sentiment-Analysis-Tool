#!/usr/bin/env python3
"""
Step 5 Phase 2: Medium Sample Testing (25-50 stocks per sector)
Fast performance validation with 0.1s delays
"""
import asyncio
import time
from typing import List, Dict, Any
from datetime import datetime

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from services.sector_aggregation_1d import SectorAggregation1D


class Phase2Validator:
    """Phase 2: Medium sample testing with optimized speed"""

    def __init__(self):
        self.aggregation_service = SectorAggregation1D()

        # Override the slow 1s delay in sector_aggregation_1d.py
        # We'll monkey patch this for Phase 2 speed testing

    def print_progress(self, current: int, total: int, sector: str, elapsed_sec: float):
        """Real-time progress indicator"""
        percent = (current / total) * 100
        bar_length = 30
        filled_length = int(bar_length * current // total)
        bar = "█" * filled_length + "-" * (bar_length - filled_length)
        rate = current / (elapsed_sec / 60) if elapsed_sec > 0 else 0
        print(
            f"\r[{bar}] {percent:5.1f}% | {sector:15} | {elapsed_sec:5.1f}s | {rate:4.1f}/min",
            end="",
            flush=True,
        )

    async def test_medium_sample(
        self, sector: str, target_stocks: int
    ) -> Dict[str, Any]:
        """Test sector with medium sample size and fast processing"""
        print(f"\n📊 Phase 2: {sector} sector ({target_stocks} stocks)")

        # Get limited stocks from sector
        with SessionLocal() as db:
            stocks = (
                db.query(StockUniverse.symbol)
                .filter(StockUniverse.sector == sector, StockUniverse.is_active == True)
                .limit(target_stocks)
                .all()
            )
            stock_symbols = [s[0] for s in stocks]

        if not stock_symbols:
            print(f"   ⚠️  No stocks found in {sector}")
            return {"success": False, "error": "No stocks found"}

        print(f"   🚀 Processing {len(stock_symbols)} stocks with 0.1s delays...")

        start_time = time.time()
        try:
            # Temporarily modify the aggregation service to use faster delays
            # This is a bit hacky but needed for Phase 2 speed testing

            # We'll call a modified version that limits stocks and uses faster delays
            result = await self.fast_sector_aggregation(sector, target_stocks)
            elapsed = time.time() - start_time

            print(f"\n   ✅ {sector}: {len(stock_symbols)} stocks in {elapsed:.1f}s")
            print(f"      Rate: {len(stock_symbols)/(elapsed/60):.1f} stocks/minute")
            print(f"      Sentiment: {result.sentiment_score:.3f}")
            print(f"      Color: {result.color_classification}")

            return {
                "success": True,
                "sector": sector,
                "stocks_tested": len(stock_symbols),
                "time_seconds": elapsed,
                "rate_per_minute": len(stock_symbols) / (elapsed / 60),
                "sentiment_score": result.sentiment_score,
                "color": result.color_classification,
            }

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n   ❌ {sector}: Failed after {elapsed:.1f}s - {e}")
            return {"success": False, "sector": sector, "error": str(e)}

    async def fast_sector_aggregation(self, sector: str, max_stocks: int):
        """Modified aggregation with faster delays and stock limits"""
        # This is a simplified version for Phase 2 testing
        # We'll modify the delay in the sector_aggregation service temporarily

        # Import and temporarily modify the delay
        import backend.services.sector_aggregation_1d as agg_module

        # Store original method
        original_method = agg_module.SectorAggregation1D.retrieve_stock_data_1d

        # Create fast version
        async def fast_retrieve_stock_data_1d(self, symbols: List[str]):
            # Limit symbols for Phase 2
            limited_symbols = symbols[:max_stocks]

            stock_data_list = []
            for i, symbol in enumerate(limited_symbols):
                try:
                    stock_data = await self.data_retrieval.get_1d_stock_data(
                        symbol, "fmp"
                    )
                    if stock_data and self._validate_stock_data(stock_data):
                        stock_data_list.append(stock_data)
                    else:
                        print(f"   ⚠️  Invalid data for {symbol}")
                except Exception as e:
                    print(f"   ❌ Error with {symbol}: {e}")
                    continue

                # FAST DELAY: 0.1 seconds instead of 1.0
                await asyncio.sleep(0.1)

                # Progress indicator
                elapsed = (
                    time.time() - self.start_time if hasattr(self, "start_time") else 0
                )
                self.validator.print_progress(
                    i + 1, len(limited_symbols), sector, elapsed
                )

            return stock_data_list

        # Monkey patch for this test
        agg_module.SectorAggregation1D.retrieve_stock_data_1d = (
            fast_retrieve_stock_data_1d
        )
        self.aggregation_service.validator = self
        self.aggregation_service.start_time = time.time()

        try:
            result = await self.aggregation_service.aggregate_sector_sentiment_1d(
                sector
            )
            return result
        finally:
            # Restore original method
            agg_module.SectorAggregation1D.retrieve_stock_data_1d = original_method

    async def run_phase2_validation(self):
        """Phase 2: Medium sample testing across all sectors"""
        print("🚀 PHASE 2: MEDIUM SAMPLE VALIDATION")
        print("=" * 60)
        print("Strategy: 25-50 stocks per sector with 0.1s delays")
        print("Goal: Fast performance validation in ~5-10 minutes")
        print("=" * 60)

        # Phase 2 sampling strategy: 25-50 stocks per sector
        test_plan = [
            ("utilities", 18),  # All (small sector)
            ("consumer_defensive", 25),  # Medium sample
            ("basic_materials", 25),  # Medium sample
            ("energy", 30),  # Medium sample
            ("real_estate", 30),  # Medium sample
            ("communication_services", 30),  # Medium sample
            ("consumer_cyclical", 40),  # Larger sample
            ("industrials", 50),  # Larger sample
            ("technology", 50),  # Larger sample
            ("financial_services", 50),  # Larger sample
            ("healthcare", 50),  # Larger sample
        ]

        results = []
        total_start = time.time()

        for i, (sector, target_stocks) in enumerate(test_plan, 1):
            print(f"\n[{i}/{len(test_plan)}] {'='*40}")

            result = await self.test_medium_sample(sector, target_stocks)
            results.append(result)

            if not result["success"]:
                print(f"\n🚨 Failure in {sector} - Continue? (stopping for now)")
                break

        # Phase 2 Summary
        total_elapsed = time.time() - total_start
        successful = [r for r in results if r.get("success")]

        print(f"\n" + "=" * 60)
        print("📊 PHASE 2 VALIDATION SUMMARY")
        print("=" * 60)

        total_stocks = sum(r.get("stocks_tested", 0) for r in successful)
        avg_rate = (
            sum(r.get("rate_per_minute", 0) for r in successful) / len(successful)
            if successful
            else 0
        )

        print(f"✅ Successful: {len(successful)}/{len(results)} sectors")
        print(f"📊 Total stocks tested: {total_stocks}")
        print(f"⏱️  Total time: {total_elapsed/60:.2f} minutes")
        print(f"📈 Average rate: {avg_rate:.1f} stocks/minute")

        if successful:
            print(f"\n🎯 SECTOR PERFORMANCE:")
            for result in successful:
                print(
                    f"   {result['sector']:20} {result['stocks_tested']:2} stocks | "
                    f"{result['time_seconds']:5.1f}s | {result['rate_per_minute']:5.1f}/min"
                )

        # Projection for full pipeline
        if avg_rate > 0:
            full_time_estimate = 2058 / avg_rate
            print(f"\n🔮 FULL PIPELINE PROJECTION:")
            print(
                f"   At {avg_rate:.1f} stocks/minute → Full 2,058 stocks = {full_time_estimate:.1f} minutes"
            )

        if len(successful) >= 9:
            print(f"\n🎉 PHASE 2: SUCCESS - Ready for Phase 3")
            return True
        else:
            print(f"\n⚠️  PHASE 2: Issues detected - Address before Phase 3")
            return False


async def main():
    """Phase 2 medium sample validation"""
    validator = Phase2Validator()
    success = await validator.run_phase2_validation()

    if success:
        print(f"\n✅ Proceed to Phase 3: Large sample testing")
    else:
        print(f"\n🔧 Fix Phase 2 issues before proceeding")


if __name__ == "__main__":
    asyncio.run(main())
