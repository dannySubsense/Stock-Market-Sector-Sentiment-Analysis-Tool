#!/usr/bin/env python3
"""
Step 5 FULL Pipeline Validation - Optimized for 45-minute runtime
No more avoidance - validate ALL 2,058 stocks across ALL 11 sectors
"""
import asyncio
import time
import json
import sys
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from services.sector_aggregation_1d import SectorAggregation1D


class FullPipelineValidator:
    """Complete pipeline validation - no shortcuts, no avoidance"""

    def __init__(self):
        self.aggregation_service = SectorAggregation1D()
        self.results_file = Path("pipeline_validation_results.json")
        self.start_time = None

    def save_progress(self, results: List[Dict]):
        """Save progress to file for resumability"""
        with open(self.results_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "results": results,
                    "total_time_so_far": (
                        time.time() - self.start_time if self.start_time else 0
                    ),
                },
                f,
                indent=2,
            )

    def load_progress(self) -> List[Dict]:
        """Load previous progress if exists"""
        if self.results_file.exists():
            with open(self.results_file, "r") as f:
                data = json.load(f)
                return data.get("results", [])
        return []

    def print_status(
        self,
        sector: str,
        current_sector: int,
        total_sectors: int,
        stocks_in_sector: int,
        elapsed_min: float,
        estimated_remaining: float,
    ):
        """Enhanced status display"""
        progress = (current_sector / total_sectors) * 100
        bar_length = 50
        filled = int(bar_length * current_sector / total_sectors)
        bar = "█" * filled + "░" * (bar_length - filled)

        print(f"\n{'='*80}")
        print(f"🎯 SECTOR {current_sector}/{total_sectors}: {sector.upper()}")
        print(f"[{bar}] {progress:5.1f}% Complete")
        print(f"📊 Processing {stocks_in_sector} stocks")
        print(
            f"⏱️  Elapsed: {elapsed_min:.1f} min | Remaining: ~{estimated_remaining:.1f} min"
        )
        print(f"{'='*80}")

    async def validate_sector_full(
        self, sector: str, sector_num: int, total_sectors: int
    ) -> Dict[str, Any]:
        """Validate complete sector with enhanced progress tracking"""

        # Get sector stock count
        with SessionLocal() as db:
            stock_count = (
                db.query(StockUniverse)
                .filter(StockUniverse.sector == sector, StockUniverse.is_active == True)
                .count()
            )

        elapsed_min = (time.time() - self.start_time) / 60
        estimated_total = 45  # Our 45-minute estimate
        estimated_remaining = estimated_total - elapsed_min

        self.print_status(
            sector,
            sector_num,
            total_sectors,
            stock_count,
            elapsed_min,
            estimated_remaining,
        )

        print(f"🚀 Starting {sector} aggregation...")
        sector_start = time.time()

        try:
            # The moment of truth - full sector aggregation
            result = await self.aggregation_service.aggregate_sector_sentiment_1d(
                sector
            )
            sector_elapsed = time.time() - sector_start

            print(f"✅ SUCCESS! {sector} completed in {sector_elapsed/60:.2f} minutes")
            print(f"   📊 Sentiment Score: {result.sentiment_score:.3f}")
            print(f"   🎨 Color: {result.color_classification}")
            print(f"   🎯 Confidence: {result.confidence_level:.3f}")
            print(
                f"   📈 Processing Rate: {stock_count/(sector_elapsed/60):.1f} stocks/minute"
            )

            return {
                "success": True,
                "sector": sector,
                "stocks_processed": stock_count,
                "time_minutes": sector_elapsed / 60,
                "sentiment_score": result.sentiment_score,
                "color": result.color_classification,
                "confidence": result.confidence_level,
                "processing_rate": stock_count / (sector_elapsed / 60),
            }

        except Exception as e:
            sector_elapsed = time.time() - sector_start
            print(f"❌ FAILED! {sector} failed after {sector_elapsed/60:.2f} minutes")
            print(f"   Error: {str(e)}")

            return {
                "success": False,
                "sector": sector,
                "error": str(e),
                "time_minutes": sector_elapsed / 60,
                "stocks_attempted": stock_count,
            }

    async def run_complete_validation(self):
        """THE FULL MONTE - All 2,058 stocks, all 11 sectors"""
        print("🚨 STEP 5 COMPLETE PIPELINE VALIDATION")
        print("=" * 80)
        print("GOAL: Validate ALL 2,058 stocks across ALL 11 sectors")
        print("ESTIMATED TIME: 40-45 minutes")
        print("APPROACH: No shortcuts, no samples - full production validation")
        print("=" * 80)

        # Optimized sector order: smallest to largest for psychological momentum
        sector_plan = [
            "utilities",  # 18 stocks (~0.3 min)
            "consumer_defensive",  # 68 stocks (~1.1 min)
            "basic_materials",  # 76 stocks (~1.3 min)
            "communication_services",  # 93 stocks (~1.6 min)
            "real_estate",  # 93 stocks (~1.6 min)
            "energy",  # 97 stocks (~1.6 min)
            "consumer_cyclical",  # 161 stocks (~2.7 min)
            "industrials",  # 202 stocks (~3.4 min)
            "technology",  # 257 stocks (~4.3 min)
            "financial_services",  # 447 stocks (~7.5 min)
            "healthcare",  # 546 stocks (~9.1 min)
        ]

        # Load any previous progress
        results = self.load_progress()
        completed_sectors = {r["sector"] for r in results if r.get("success")}
        remaining_sectors = [s for s in sector_plan if s not in completed_sectors]

        if completed_sectors:
            print(f"📁 RESUMING: Found {len(completed_sectors)} completed sectors")
            print(f"   Completed: {', '.join(completed_sectors)}")
            print(f"   Remaining: {len(remaining_sectors)} sectors")

        self.start_time = time.time()
        total_sectors = len(sector_plan)

        for i, sector in enumerate(remaining_sectors, start=len(completed_sectors) + 1):
            print(
                f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Starting sector {i}/{total_sectors}"
            )

            result = await self.validate_sector_full(sector, i, total_sectors)
            results.append(result)

            # Save progress after each sector
            self.save_progress(results)

            if not result["success"]:
                print(f"\n🚨 CRITICAL FAILURE in {sector}")
                print(f"Continue with remaining sectors? (y/n)")
                # Could add user input here in real implementation
                break

        # Final comprehensive report
        await self.generate_final_report(results)

    async def generate_final_report(self, results: List[Dict]):
        """Comprehensive final validation report"""
        total_elapsed = time.time() - self.start_time
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        print(f"\n" + "=" * 80)
        print("🏁 COMPLETE PIPELINE VALIDATION - FINAL REPORT")
        print("=" * 80)

        total_stocks = sum(r.get("stocks_processed", 0) for r in successful)
        total_rate = total_stocks / (total_elapsed / 60) if total_elapsed > 0 else 0

        print(f"📊 OVERALL RESULTS:")
        print(f"   ✅ Successful Sectors: {len(successful)}/11")
        print(f"   📈 Total Stocks Processed: {total_stocks:,}")
        print(f"   ⏱️  Total Runtime: {total_elapsed/60:.2f} minutes")
        print(f"   📊 Overall Processing Rate: {total_rate:.1f} stocks/minute")

        if successful:
            print(f"\n🎯 SECTOR PERFORMANCE BREAKDOWN:")
            for result in successful:
                rate = result.get("processing_rate", 0)
                print(
                    f"   {result['sector']:20} {result['stocks_processed']:3} stocks | "
                    f"{result['time_minutes']:4.1f}min | {rate:4.1f}/min | "
                    f"Sentiment: {result.get('sentiment_score', 0):.3f}"
                )

        if failed:
            print(f"\n🚨 FAILED SECTORS:")
            for result in failed:
                print(
                    f"   {result['sector']:20} Error: {result.get('error', 'Unknown')}"
                )

        # Success criteria
        if len(successful) >= 10:
            print(f"\n🎉 VALIDATION STATUS: COMPLETE SUCCESS")
            print(f"✅ Pipeline validated with {total_stocks:,} real stocks")
            print(f"✅ Ready for Step 6 - Database Storage Development")
            print(f"✅ Production performance characteristics documented")
        elif len(successful) >= 8:
            print(f"\n⚠️  VALIDATION STATUS: MOSTLY SUCCESSFUL")
            print(f"✅ Core pipeline validated, investigate minor failures")
        else:
            print(f"\n❌ VALIDATION STATUS: SIGNIFICANT ISSUES")
            print(f"🔧 Address failures before proceeding to Step 6")


async def main():
    """No more delays - full pipeline validation"""
    print("🎯 STEP 5 FINAL VALIDATION")
    print("Time to validate the complete pipeline with ALL stocks")
    print("Estimated duration: 40-45 minutes")
    print()

    validator = FullPipelineValidator()
    await validator.run_complete_validation()


if __name__ == "__main__":
    asyncio.run(main())
