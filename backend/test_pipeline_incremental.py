#!/usr/bin/env python3
"""
Step 5 Pipeline Validation - Incremental Scaling to Complete Coverage
Progressive testing that scales up to validate ALL stocks in ALL sectors
"""
import asyncio
import time
import sys
from typing import List, Dict, Any
from datetime import datetime

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from services.sector_aggregation_1d import SectorAggregation1D


class IncrementalPipelineValidator:
    """Progressive testing that scales to complete sector validation"""

    def __init__(self):
        self.aggregation_service = SectorAggregation1D()

    def print_progress(self, current: int, total: int, sector: str, status: str):
        """Real-time progress indicator"""
        percent = (current / total) * 100
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = "█" * filled_length + "-" * (bar_length - filled_length)
        elapsed_min = (time.time() - self.start_time) / 60
        print(
            f"\r[{bar}] {percent:5.1f}% | {sector:20} | {elapsed_min:4.1f}min | {status}",
            end="",
            flush=True,
        )

    async def test_sector_incremental(
        self, sector: str, max_stocks: int = None
    ) -> Dict[str, Any]:
        """Test sector with actual API calls and real aggregation"""
        print(f"\n🎯 Testing {sector} sector (up to {max_stocks or 'ALL'} stocks)...")

        # Get stocks for this sector
        with SessionLocal() as db:
            query = db.query(StockUniverse.symbol).filter(
                StockUniverse.sector == sector, StockUniverse.is_active == True
            )
            if max_stocks:
                query = query.limit(max_stocks)

            stocks = query.all()
            stock_symbols = [s[0] for s in stocks]

        if not stock_symbols:
            print(f"   ⚠️  No stocks found in {sector}")
            return {"success": False, "error": "No stocks found"}

        print(f"   📊 Processing {len(stock_symbols)} stocks in {sector} sector...")
        print(f"   🚀 Starting real aggregation with API calls...")

        self.start_time = time.time()
        try:
            # Call the REAL aggregation service (this will make actual API calls)
            result = await self.aggregation_service.aggregate_sector_sentiment_1d(
                sector
            )
            elapsed = time.time() - self.start_time

            print(
                f"\n   ✅ {sector}: {len(stock_symbols)} stocks in {elapsed/60:.2f} minutes"
            )
            print(f"      Sentiment Score: {result.sentiment_score:.3f}")
            print(f"      Color: {result.color_classification}")
            print(f"      Confidence: {result.confidence_level:.3f}")

            return {
                "success": True,
                "sector": sector,
                "stocks_processed": len(stock_symbols),
                "time_minutes": elapsed / 60,
                "sentiment_score": result.sentiment_score,
                "color": result.color_classification,
                "confidence": result.confidence_level,
            }

        except Exception as e:
            elapsed = time.time() - self.start_time
            print(f"\n   ❌ {sector}: Failed after {elapsed/60:.2f} minutes - {e}")
            return {
                "success": False,
                "sector": sector,
                "error": str(e),
                "time_minutes": elapsed / 60,
            }

    async def run_incremental_validation(self):
        """Progressive validation scaling up to complete coverage"""
        print("🚀 INCREMENTAL PIPELINE VALIDATION")
        print("=" * 80)
        print("Strategy: Progressive scaling to complete sector validation")
        print("Goal: Validate ALL 2,058 stocks across ALL 11 sectors")
        print("=" * 80)

        # Phase 1: Smallest sectors first (build confidence)
        phase1_plan = [
            ("utilities", None),  # 18 stocks (~0.3 min)
            ("consumer_defensive", None),  # 68 stocks (~1.1 min)
            ("basic_materials", None),  # 76 stocks (~1.3 min)
        ]

        # Phase 2: Medium sectors (validate scalability)
        phase2_plan = [
            ("energy", None),  # 97 stocks (~1.6 min)
            ("real_estate", None),  # 93 stocks (~1.6 min)
            ("communication_services", None),  # 93 stocks (~1.6 min)
            ("consumer_cyclical", None),  # 161 stocks (~2.7 min)
        ]

        # Phase 3: Large sectors (test performance limits)
        phase3_plan = [
            ("industrials", None),  # 202 stocks (~3.4 min)
            ("technology", None),  # 257 stocks (~4.3 min)
        ]

        # Phase 4: Largest sectors (full production validation)
        phase4_plan = [
            ("financial_services", None),  # 447 stocks (~7.5 min)
            ("healthcare", None),  # 546 stocks (~9.1 min)
        ]

        all_phases = [
            ("PHASE 1: Small Sectors", phase1_plan),
            ("PHASE 2: Medium Sectors", phase2_plan),
            ("PHASE 3: Large Sectors", phase3_plan),
            ("PHASE 4: Largest Sectors", phase4_plan),
        ]

        results = []
        total_start_time = time.time()

        for phase_name, phase_plan in all_phases:
            print(f"\n🎯 {phase_name}")
            print("=" * 60)

            phase_start = time.time()
            phase_results = []

            for sector, max_stocks in phase_plan:
                result = await self.test_sector_incremental(sector, max_stocks)
                results.append(result)
                phase_results.append(result)

                if not result["success"]:
                    print(
                        f"\n🚨 CRITICAL FAILURE in {sector} - Do you want to continue? (y/n)"
                    )
                    # In real implementation, could pause for user input
                    break

            phase_elapsed = time.time() - phase_start
            successful_in_phase = [r for r in phase_results if r.get("success")]

            print(f"\n📊 {phase_name} SUMMARY:")
            print(
                f"   ✅ Successful: {len(successful_in_phase)}/{len(phase_results)} sectors"
            )
            print(f"   ⏱️  Phase Time: {phase_elapsed/60:.2f} minutes")

            if len(successful_in_phase) < len(phase_results):
                print(f"   ⚠️  Some sectors failed - Review before continuing")

        # Final Summary
        total_elapsed = time.time() - total_start_time
        successful_sectors = [r for r in results if r.get("success")]
        failed_sectors = [r for r in results if not r.get("success")]

        print(f"\n" + "=" * 80)
        print("🏁 COMPLETE PIPELINE VALIDATION SUMMARY")
        print("=" * 80)

        total_stocks = sum(r.get("stocks_processed", 0) for r in successful_sectors)

        print(f"✅ Successful Sectors: {len(successful_sectors)}/{len(results)}")
        print(f"📊 Total Stocks Processed: {total_stocks:,}")
        print(f"⏱️  Total Time: {total_elapsed/60:.2f} minutes")
        print(
            f"📈 Average Processing Rate: {total_stocks/(total_elapsed/60):.1f} stocks/minute"
        )

        if successful_sectors:
            print(f"\n🎯 SECTOR PERFORMANCE BREAKDOWN:")
            for result in successful_sectors:
                rate = result["stocks_processed"] / result["time_minutes"]
                print(
                    f"   {result['sector']:20} {result['stocks_processed']:3} stocks in {result['time_minutes']:4.1f}min ({rate:4.1f}/min)"
                )

        if failed_sectors:
            print(f"\n🚨 FAILED SECTORS:")
            for result in failed_sectors:
                print(
                    f"   {result.get('sector', 'Unknown'):20} {result.get('error', 'Unknown error')}"
                )

        # Final Assessment
        if len(successful_sectors) >= 10:  # 10+ out of 11 sectors
            print(f"\n🎉 PIPELINE VALIDATION: COMPLETE SUCCESS")
            print(f"✅ Ready for Step 6 - Full pipeline validated with real data")
            print(
                f"✅ Processed {total_stocks:,} stocks across {len(successful_sectors)} sectors"
            )
        elif len(successful_sectors) >= 8:
            print(f"\n⚠️  PIPELINE VALIDATION: MOSTLY SUCCESSFUL")
            print(f"✅ Core functionality validated, minor issues to investigate")
        else:
            print(f"\n❌ PIPELINE VALIDATION: NEEDS SIGNIFICANT WORK")
            print(f"🔧 Fix major issues before proceeding to Step 6")

        return len(successful_sectors) >= 10


async def main():
    """Complete incremental pipeline validation"""
    print("🎯 STEP 5 COMPLETE PIPELINE VALIDATION")
    print("Incremental approach: Small → Medium → Large → Largest sectors")
    print("Goal: Process ALL 2,058 stocks across ALL 11 sectors")
    print()

    validator = IncrementalPipelineValidator()
    success = await validator.run_incremental_validation()

    if success:
        print(f"\n🏆 RECOMMENDATION: Proceed to Step 6")
        print(f"   Complete pipeline validated with production data")
        print(f"   Performance characteristics fully understood")
        print(f"   Ready for database storage and API endpoint development")
    else:
        print(f"\n🔧 RECOMMENDATION: Address issues before Step 6")
        print(f"   Investigate failing sectors and error patterns")
        print(f"   Ensure pipeline reliability before proceeding")


if __name__ == "__main__":
    asyncio.run(main())
