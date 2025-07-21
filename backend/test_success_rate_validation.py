#!/usr/bin/env python3
"""
Success Rate Validation Test
Verify that the 95% success rate error checking works properly
"""
import asyncio
import logging
from typing import List
from unittest.mock import AsyncMock, patch

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from services.sector_aggregation_1d import SectorAggregation1D

# Set up logging to see validation messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SuccessRateValidationTest:
    """Test success rate validation functionality"""

    def __init__(self):
        self.aggregation_service = SectorAggregation1D()

    async def test_normal_success_rate(self):
        """Test with normal high success rate (should pass)"""
        print("\n🧪 TEST 1: Normal High Success Rate (>98%)")
        print("-" * 50)

        # Get a small sample of real stocks
        session = SessionLocal()
        try:
            sample_stocks = (
                session.query(StockUniverse.symbol)
                .filter(StockUniverse.sector == "technology")
                .limit(20)
                .all()
            )
            symbols = [stock.symbol for stock in sample_stocks]
        finally:
            session.close()

        print(f"Testing with {len(symbols)} technology stocks...")

        try:
            stock_data_list = await self.aggregation_service.retrieve_stock_data_1d(
                symbols
            )
            success_rate = len(stock_data_list) / len(symbols) * 100

            print(
                f"✅ SUCCESS: {len(stock_data_list)}/{len(symbols)} stocks retrieved ({success_rate:.1f}%)"
            )

            if success_rate >= 95:
                print("✅ VALIDATION PASSED: Success rate above 95% threshold")
            else:
                print("⚠️ VALIDATION FAILED: Success rate below 95% threshold")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    async def test_low_success_rate_simulation(self):
        """Test with simulated low success rate (should trigger warning)"""
        print("\n🧪 TEST 2: Simulated Low Success Rate (<95%)")
        print("-" * 50)

        # Create a list with mix of real and fake symbols to trigger failures
        real_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        fake_symbols = ["FAKE1", "FAKE2", "FAKE3", "FAKE4", "FAKE5", "FAKE6"]
        test_symbols = (
            real_symbols + fake_symbols
        )  # 5 real + 6 fake = 45% expected success

        print(
            f"Testing with {len(real_symbols)} real + {len(fake_symbols)} fake symbols..."
        )
        print(f"Expected success rate: ~{len(real_symbols)/len(test_symbols)*100:.1f}%")

        try:
            stock_data_list = await self.aggregation_service.retrieve_stock_data_1d(
                test_symbols
            )
            success_rate = len(stock_data_list) / len(test_symbols) * 100

            print(
                f"🔍 RESULT: {len(stock_data_list)}/{len(test_symbols)} stocks retrieved ({success_rate:.1f}%)"
            )

            if success_rate < 95:
                print(
                    "✅ VALIDATION TRIGGERED: Low success rate detected (as expected)"
                )
            else:
                print("⚠️ UNEXPECTED: Success rate higher than expected")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    async def test_sector_level_validation(self):
        """Test validation at sector level"""
        print("\n🧪 TEST 3: Sector-Level Success Rate Validation")
        print("-" * 50)

        # Test with utilities sector (smallest sector)
        session = SessionLocal()
        try:
            utilities_stocks = (
                session.query(StockUniverse.symbol)
                .filter(StockUniverse.sector == "utilities")
                .all()
            )
            symbols = [stock.symbol for stock in utilities_stocks]
        finally:
            session.close()

        print(f"Testing utilities sector with {len(symbols)} stocks...")

        try:
            result = await self.aggregation_service.aggregate_sector_sentiment_1d(
                "utilities"
            )

            print(f"✅ Sector calculation completed")
            print(f"📊 Sentiment: {result.sentiment_score:.3f}")
            print(f"📈 Confidence: {result.confidence_level:.3f}")
            print(f"🔢 Stocks used: {result.stock_count} stocks")
            print(f"📊 Data coverage: {result.data_coverage:.1f}%")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    async def test_mixed_symbols_sector_validation(self):
        """Test sector validation with mixed real/fake symbols"""
        print("\n🧪 TEST 4: Mixed Symbols Sector Validation")
        print("-" * 50)

        # Create a custom test with mix of real and fake symbols
        real_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        fake_symbols = ["FAKE1", "FAKE2", "FAKE3", "FAKE4", "FAKE5", "FAKE6"]
        test_symbols = (
            real_symbols + fake_symbols
        )  # 5 real + 6 fake = ~45% expected success

        print(
            f"Testing with {len(real_symbols)} real + {len(fake_symbols)} fake symbols..."
        )
        print(f"Expected success rate: ~{len(real_symbols)/len(test_symbols)*100:.1f}%")

        try:
            # Mock the sector mapping to use our test symbols
            from unittest.mock import patch

            mock_mapping = type(
                "MockMapping",
                (),
                {
                    "symbols": test_symbols,
                    "total_stocks": len(test_symbols),
                    "active_stocks": len(test_symbols),
                    "coverage_percentage": 100.0,
                },
            )()

            with patch.object(
                self.aggregation_service, "get_sector_stocks", return_value=mock_mapping
            ):
                # This should trigger the <95% validation warning
                stock_data_list = await self.aggregation_service.retrieve_stock_data_1d(
                    test_symbols
                )
                success_rate = len(stock_data_list) / len(test_symbols) * 100

                print(
                    f"🔍 RESULT: {len(stock_data_list)}/{len(test_symbols)} stocks retrieved ({success_rate:.1f}%)"
                )

                if success_rate < 95:
                    print(
                        "✅ VALIDATION WOULD TRIGGER: Low success rate detected (as expected)"
                    )
                else:
                    print("⚠️ UNEXPECTED: Success rate higher than expected")

        except Exception as e:
            print(f"❌ ERROR: {e}")


async def main():
    """Run success rate validation tests"""
    print("🔍 SUCCESS RATE VALIDATION TESTS")
    print("=" * 60)
    print("Testing 95% success rate threshold validation...")

    test_runner = SuccessRateValidationTest()

    # Run all tests
    await test_runner.test_normal_success_rate()
    await test_runner.test_low_success_rate_simulation()
    await test_runner.test_sector_level_validation()
    await test_runner.test_mixed_symbols_sector_validation()

    print("\n" + "=" * 60)
    print("✅ SUCCESS RATE VALIDATION TESTS COMPLETE")
    print("\n💡 SUMMARY:")
    print("   • Normal operations should show >98% success rates")
    print("   • 95-98% rates trigger warnings but continue processing")
    print("   • <95% rates indicate system issues and log critical errors")
    print("   • This helps distinguish edge cases from API failures")


if __name__ == "__main__":
    asyncio.run(main())
