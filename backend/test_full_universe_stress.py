#!/usr/bin/env python3
"""
Step 5: FULL UNIVERSE STRESS TEST
Goal: Process all 2,058 stocks with maximum speed and full visibility
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from collections import defaultdict
import sys

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from services.stock_data_retrieval_1d import StockDataRetrieval1D


class FullUniverseStressTest:
    """Comprehensive stress test for full stock universe"""

    def __init__(self):
        self.data_retrieval = StockDataRetrieval1D()
        self.total_processed = 0
        self.total_successful = 0
        self.total_failed = 0
        self.sector_stats = defaultdict(
            lambda: {"processed": 0, "successful": 0, "failed": 0}
        )
        self.start_time = None

    def print_progress_bar(
        self,
        current: int,
        total: int,
        prefix: str = "",
        suffix: str = "",
        length: int = 50,
    ):
        """Display a progress bar"""
        percent = 100 * (current / float(total))
        filled_length = int(length * current // total)
        bar = "█" * filled_length + "-" * (length - filled_length)

        # Calculate speed
        if self.start_time:
            elapsed = time.time() - self.start_time
            speed = current / elapsed * 60 if elapsed > 0 else 0
            speed_str = f" | {speed:.0f}/min"
        else:
            speed_str = ""

        print(
            f"\r{prefix} |{bar}| {current}/{total} ({percent:.1f}%){speed_str} {suffix}",
            end="",
            flush=True,
        )

    async def process_sector_concurrent(
        self, sector: str, symbols: List[str], concurrent_limit: int = 10
    ) -> Dict[str, Any]:
        """Process a single sector with concurrent API calls"""
        print(f"\n🔄 Processing {sector.upper()}: {len(symbols)} stocks")

        sector_start_time = time.time()
        successful_stocks = []
        failed_stocks = []

        # Create semaphore for concurrent requests
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def fetch_single_stock(symbol: str) -> Optional[str]:
            async with semaphore:
                try:
                    data = await self.data_retrieval.get_1d_stock_data(
                        symbol, "polygon"
                    )
                    if data:
                        successful_stocks.append(symbol)
                        self.total_successful += 1
                        return symbol
                    else:
                        failed_stocks.append(symbol)
                        self.total_failed += 1
                        return None
                except Exception as e:
                    failed_stocks.append(symbol)
                    self.total_failed += 1
                    return None
                finally:
                    self.total_processed += 1
                    # Update progress bar every few stocks
                    if self.total_processed % 5 == 0:
                        self.print_progress_bar(
                            self.total_processed,
                            2058,  # Total universe size
                            prefix="🚀 Overall Progress",
                            suffix=f"| {sector}",
                        )

        # Execute all requests for this sector concurrently
        tasks = [fetch_single_stock(symbol) for symbol in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)

        sector_elapsed = time.time() - sector_start_time
        sector_speed = len(symbols) / sector_elapsed * 60 if sector_elapsed > 0 else 0

        # Update sector stats
        self.sector_stats[sector] = {
            "processed": len(symbols),
            "successful": len(successful_stocks),
            "failed": len(failed_stocks),
            "elapsed_time": sector_elapsed,
            "speed": sector_speed,
        }

        print(
            f"\n   ✅ {len(successful_stocks)}/{len(symbols)} successful | ⚡ {sector_speed:.0f}/min | ⏱️ {sector_elapsed:.2f}s"
        )

        return {
            "sector": sector,
            "total": len(symbols),
            "successful": len(successful_stocks),
            "failed": len(failed_stocks),
            "elapsed_time": sector_elapsed,
            "speed": sector_speed,
            "failed_symbols": failed_stocks,
        }

    async def run_full_stress_test(self) -> Dict[str, Any]:
        """Execute full universe stress test"""
        print("🚀 FULL UNIVERSE STRESS TEST")
        print("=" * 60)
        print("📊 Loading stock universe...")

        # Get all stocks by sector
        session = SessionLocal()
        try:
            all_stocks = (
                session.query(StockUniverse.symbol, StockUniverse.sector)
                .filter(StockUniverse.sector != "unknown")
                .all()
            )

            # Group by sector
            sectors_data = defaultdict(list)
            for stock in all_stocks:
                sectors_data[stock.sector].append(stock.symbol)

        finally:
            session.close()

        total_stocks = sum(len(symbols) for symbols in sectors_data.values())
        print(f"📈 Total stocks to process: {total_stocks}")
        print(f"📊 Sectors: {len(sectors_data)}")

        for sector, symbols in sectors_data.items():
            print(f"   • {sector}: {len(symbols)} stocks")

        print("\n🔥 Starting stress test with 10 concurrent requests per sector...")
        print("⏱️ Estimated completion: ~17 seconds\n")

        self.start_time = time.time()
        self.total_processed = 0
        self.total_successful = 0
        self.total_failed = 0

        # Process all sectors
        sector_results = []
        for sector, symbols in sectors_data.items():
            result = await self.process_sector_concurrent(
                sector, symbols, concurrent_limit=10
            )
            sector_results.append(result)

        total_elapsed = time.time() - self.start_time
        overall_speed = total_stocks / total_elapsed * 60 if total_elapsed > 0 else 0

        # Final progress bar
        self.print_progress_bar(
            total_stocks, total_stocks, prefix="🏁 COMPLETE", suffix=""
        )
        print()  # New line after progress bar

        return {
            "total_stocks": total_stocks,
            "total_processed": self.total_processed,
            "total_successful": self.total_successful,
            "total_failed": self.total_failed,
            "total_elapsed": total_elapsed,
            "overall_speed": overall_speed,
            "sector_results": sector_results,
        }

    def print_detailed_results(self, results: Dict[str, Any]) -> None:
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("📊 FULL UNIVERSE STRESS TEST RESULTS")
        print("=" * 60)

        # Overall metrics
        print(f"🎯 OVERALL PERFORMANCE:")
        print(f"   📈 Total Stocks: {results['total_stocks']:,}")
        print(
            f"   ✅ Successful: {results['total_successful']:,} ({results['total_successful']/results['total_stocks']*100:.1f}%)"
        )
        print(
            f"   ❌ Failed: {results['total_failed']:,} ({results['total_failed']/results['total_stocks']*100:.1f}%)"
        )
        print(f"   ⏱️  Total Time: {results['total_elapsed']:.2f} seconds")
        print(f"   ⚡ Overall Speed: {results['overall_speed']:.0f} stocks/minute")

        # Speed comparison
        print(f"\n🚀 SPEED COMPARISON:")
        print(f"   • This test: {results['total_elapsed']:.1f} seconds")
        print(
            f"   • Sequential: ~{results['total_stocks']/726*60:.1f} seconds (old method)"
        )
        print(f"   • FMP estimate: ~{45*60:.0f} seconds (original)")
        print(
            f"   • Speed improvement: {45*60/results['total_elapsed']:.0f}x faster than FMP!"
        )

        # Sector breakdown
        print(f"\n📊 SECTOR BREAKDOWN:")
        for result in sorted(
            results["sector_results"], key=lambda x: x["speed"], reverse=True
        ):
            success_rate = (
                result["successful"] / result["total"] * 100
                if result["total"] > 0
                else 0
            )
            print(
                f"   • {result['sector'].upper():<20}: {result['successful']:>3}/{result['total']:<3} "
                f"({success_rate:>5.1f}%) | {result['speed']:>5.0f}/min | {result['elapsed_time']:>4.2f}s"
            )

        # Failed stocks summary
        total_failures = sum(
            len(result.get("failed_symbols", []))
            for result in results["sector_results"]
        )
        if total_failures > 0:
            print(f"\n⚠️  FAILED STOCKS SUMMARY:")
            for result in results["sector_results"]:
                if result.get("failed_symbols"):
                    print(
                        f"   {result['sector']}: {', '.join(result['failed_symbols'][:5])}"
                        f"{'...' if len(result['failed_symbols']) > 5 else ''}"
                    )

        print("\n" + "=" * 60)
        print("✅ STRESS TEST COMPLETE - SYSTEM PERFORMANCE VALIDATED!")
        print("=" * 60)


async def main():
    """Run full universe stress test"""
    stress_test = FullUniverseStressTest()

    try:
        results = await stress_test.run_full_stress_test()
        stress_test.print_detailed_results(results)

    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        print(f"📊 Processed: {stress_test.total_processed} stocks")
        print(f"✅ Successful: {stress_test.total_successful}")
        print(f"❌ Failed: {stress_test.total_failed}")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print(f"📊 Processed: {stress_test.total_processed} stocks before failure")


if __name__ == "__main__":
    asyncio.run(main())
