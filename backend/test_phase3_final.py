#!/usr/bin/env python3
"""Phase 3 Final Test: Complete Analysis Scheduler Integration"""

import asyncio
import sys
import os
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.analysis_scheduler import get_analysis_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("🔍 Testing Phase 3: Analysis Scheduler FMP Batch Integration")

    scheduler = get_analysis_scheduler()

    # Test quick analysis (should be fast with stored data)
    logger.info("Testing quick on-demand analysis...")
    result = await scheduler.run_on_demand_analysis("quick")

    status = result.get("status")
    sectors = result.get("sectors_analyzed", 0)
    duration = result.get("duration_seconds", 0)

    logger.info(f"✅ Analysis Status: {status}")
    logger.info(f"✅ Sectors Analyzed: {sectors}")
    logger.info(f"✅ Duration: {duration:.2f}s")

    if status == "success" and duration < 30:
        print("\n🎉 PHASE 3 FINAL TEST: SUCCESS!")
        print(f"✅ Fast analysis: {duration:.2f}s for {sectors} sectors")
        print("✅ FMP batch workflow integrated successfully")
        return True
    else:
        print(
            f"\n❌ PHASE 3 FINAL TEST: ISSUES - Status: {status}, Duration: {duration:.2f}s"
        )
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
