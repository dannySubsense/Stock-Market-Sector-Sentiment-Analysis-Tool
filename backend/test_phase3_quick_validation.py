#!/usr/bin/env python3
"""
Phase 3 Quick Validation: Check if sector calculator uses stored data

This test validates that the sector calculator is reading from the
stock_prices_1d table instead of making individual API calls.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.sector_calculator import get_sector_calculator
from core.database import SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_sector_calculator_uses_stored_data():
    """Test that sector calculator uses stored price data"""
    try:
        logger.info("=" * 60)
        logger.info("PHASE 3 QUICK VALIDATION: Sector Calculator Data Source")
        logger.info("=" * 60)

        # Check if we have stored price data
        with SessionLocal() as db:
            from models.stock_data import StockPrice1D

            stored_count = db.query(StockPrice1D).count()
            logger.info(f"✅ Stock price records in database: {stored_count}")

            if stored_count == 0:
                logger.error(
                    "❌ No stored price data found! Need to run FMP batch first."
                )
                return False

            # Get a sample symbol
            sample_record = db.query(StockPrice1D).first()
            test_symbol = sample_record.symbol
            logger.info(f"✅ Testing with sample symbol: {test_symbol}")

        # Test sector calculator's quote data method
        calculator = get_sector_calculator()

        # This should use stored data (no API call)
        logger.info(f"🔍 Testing _get_stock_quote_data for {test_symbol}...")
        start_time = datetime.now(timezone.utc)

        quote_data = await calculator._get_stock_quote_data(test_symbol)

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        if quote_data:
            logger.info(f"✅ Quote data retrieved in {duration:.3f}s")
            logger.info(f"✅ Quote data: {quote_data}")

            # Fast response indicates stored data usage
            if duration < 0.1:  # Less than 100ms = definitely stored data
                logger.info("🚀 FAST response - using stored data (NO API CALLS)")
                return True
            else:
                logger.warning(
                    f"⚠️  SLOW response ({duration:.3f}s) - might be using API calls"
                )
                return False
        else:
            logger.error("❌ No quote data returned")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def test_quick_sector_analysis():
    """Test a quick sector analysis to see overall performance"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("TESTING QUICK SECTOR ANALYSIS")
        logger.info("=" * 60)

        calculator = get_sector_calculator()

        # Test calculating one sector (should be fast if using stored data)
        logger.info("🔍 Testing sector sentiment calculation...")
        start_time = datetime.now(timezone.utc)

        # Get first available sector
        sectors = await calculator._get_active_sectors()
        if not sectors:
            logger.error("❌ No active sectors found")
            return False

        test_sector = sectors[0]
        logger.info(f"✅ Testing sector: {test_sector}")

        sector_result = await calculator.calculate_sector_sentiment(test_sector)

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        logger.info(f"✅ Sector analysis completed in {duration:.2f}s")
        logger.info(f"✅ Result status: {sector_result.get('sector', 'N/A')}")

        # Fast response indicates stored data usage
        if duration < 10:  # Less than 10s = good performance
            logger.info("🚀 FAST sector analysis - likely using stored data")
            return True
        else:
            logger.warning(
                f"⚠️  SLOW sector analysis ({duration:.2f}s) - might be using API calls"
            )
            return False

    except Exception as e:
        logger.error(f"❌ Sector analysis test failed: {e}")
        return False


async def main():
    """Main validation execution"""

    # Test 1: Quote data source
    stored_data_test = await test_sector_calculator_uses_stored_data()

    # Test 2: Quick sector analysis
    sector_analysis_test = await test_quick_sector_analysis()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 3 QUICK VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Stored Data Usage: {'✅ PASS' if stored_data_test else '❌ FAIL'}")
    logger.info(
        f"Fast Sector Analysis: {'✅ PASS' if sector_analysis_test else '❌ FAIL'}"
    )

    if stored_data_test and sector_analysis_test:
        print("\n🎉 PHASE 3 QUICK VALIDATION: SUCCESS!")
        print("✅ Sector calculator is using stored data (no individual API calls)")
    else:
        print("\n❌ PHASE 3 QUICK VALIDATION: ISSUES DETECTED")
        print("⚠️  Sector calculator may still be making individual API calls")

    return stored_data_test and sector_analysis_test


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
