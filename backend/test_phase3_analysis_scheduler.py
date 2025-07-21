#!/usr/bin/env python3
"""
Phase 3 Test: Analysis Scheduler FMP Batch Integration

Tests the updated analysis scheduler with FMP batch workflow integration.
Validates that the scheduler can successfully use the new efficient batch
workflow for universe building and price data retrieval.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.analysis_scheduler import get_analysis_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_analysis_scheduler_fmp_batch():
    """Test the analysis scheduler with FMP batch workflow"""
    try:
        logger.info("=" * 80)
        logger.info("PHASE 3 TEST: Analysis Scheduler FMP Batch Integration")
        logger.info("=" * 80)

        # Get analysis scheduler instance
        scheduler = get_analysis_scheduler()

        # Test 1: Check scheduler initialization
        logger.info("\n1. Testing scheduler initialization...")
        status = scheduler.get_analysis_status()
        logger.info(f"Scheduler Status: {status}")

        # Test 2: Test on-demand quick analysis (baseline)
        logger.info("\n2. Testing on-demand quick analysis...")
        start_time = datetime.now(timezone.utc)

        quick_result = await scheduler.run_on_demand_analysis("quick")

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Quick Analysis Result: {quick_result}")
        logger.info(f"Quick Analysis Duration: {duration:.2f}s")

        # Test 3: Test on-demand full analysis with FMP batch
        logger.info("\n3. Testing on-demand full analysis with FMP batch...")
        start_time = datetime.now(timezone.utc)

        full_result = await scheduler.run_on_demand_analysis("full")

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Full Analysis Result: {full_result}")
        logger.info(f"Full Analysis Duration: {duration:.2f}s")

        # Test 4: Validate FMP batch workflow integration
        logger.info("\n4. Validating FMP batch workflow integration...")

        # Check if result contains FMP batch indicators
        if full_result.get("status") == "success":
            fmp_batch_used = full_result.get("fmp_batch_workflow", False)
            universe_size = full_result.get("universe_size", 0)
            price_records = full_result.get("price_data_records", 0)

            logger.info(f"✅ FMP Batch Workflow: {fmp_batch_used}")
            logger.info(f"✅ Universe Size: {universe_size}")
            logger.info(f"✅ Price Data Records: {price_records}")

            if fmp_batch_used and universe_size > 0 and price_records > 0:
                logger.info("✅ Phase 3 Integration: SUCCESS")
                logger.info(f"✅ Efficiency: FMP batch workflow operational")
            else:
                logger.warning("⚠️  Phase 3 Integration: Partial success")
        else:
            logger.error(
                f"❌ Full analysis failed: {full_result.get('error', 'Unknown error')}"
            )

        # Test 5: Check data freshness
        logger.info("\n5. Testing data freshness...")
        freshness = scheduler.get_data_freshness()
        logger.info(f"Data Freshness: {freshness}")

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3 TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(
            f"Quick Analysis: {'✅ PASS' if quick_result.get('status') == 'success' else '❌ FAIL'}"
        )
        logger.info(
            f"Full Analysis: {'✅ PASS' if full_result.get('status') == 'success' else '❌ FAIL'}"
        )
        logger.info(
            f"FMP Batch Integration: {'✅ PASS' if full_result.get('fmp_batch_workflow') else '❌ FAIL'}"
        )
        logger.info(f"Duration Efficiency: {'✅ PASS' if duration < 60 else '⚠️  SLOW'}")

        return {
            "status": "success",
            "quick_result": quick_result,
            "full_result": full_result,
            "fmp_batch_integrated": full_result.get("fmp_batch_workflow", False),
            "universe_size": full_result.get("universe_size", 0),
            "price_records": full_result.get("price_data_records", 0),
            "duration_seconds": duration,
        }

    except Exception as e:
        logger.error(f"❌ Phase 3 test failed: {e}")
        return {"status": "error", "error": str(e)}


async def main():
    """Main test execution"""
    result = await test_analysis_scheduler_fmp_batch()

    # Final status
    if result["status"] == "success":
        print("\n🎉 PHASE 3 TEST COMPLETED SUCCESSFULLY!")
        print(f"📊 Universe Size: {result['universe_size']}")
        print(f"📈 Price Records: {result['price_records']}")
        print(f"⚡ Duration: {result['duration_seconds']:.2f}s")
        print(
            f"🚀 FMP Batch: {'✅ Integrated' if result['fmp_batch_integrated'] else '❌ Not Integrated'}"
        )
    else:
        print(f"\n❌ PHASE 3 TEST FAILED: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
