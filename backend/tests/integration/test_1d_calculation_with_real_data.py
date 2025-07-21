"""
Integration Test: 1D Calculation with Real API Data
Tests the complete pipeline: API retrieval → 1D calculation → results
"""

import asyncio
import pytest
from services.stock_data_retrieval_1d import StockDataRetrieval1D
from services.sector_performance_1d import SectorPerformanceCalculator1D
from config.volatility_weights import get_weight_for_sector


class Test1DCalculationWithRealData:
    """Integration test for complete 1D calculation pipeline"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_1d_calculation_pipeline(self):
        """
        Test complete pipeline: API → data retrieval → 1D calculation
        This validates that Step 1 + Step 2 work together
        """
        print("\n" + "=" * 60)
        print("COMPLETE 1D CALCULATION PIPELINE TEST")
        print("=" * 60)

        # Initialize services
        retrieval_service = StockDataRetrieval1D()

        # Get volatility multipliers for calculator
        volatility_multipliers = {
            "technology": get_weight_for_sector("technology"),
            "healthcare": get_weight_for_sector("healthcare"),
            "energy": get_weight_for_sector("energy"),
            "financial": get_weight_for_sector("financial"),
            "consumer_discretionary": get_weight_for_sector("consumer_discretionary"),
            "industrials": get_weight_for_sector("industrials"),
            "materials": get_weight_for_sector("materials"),
            "utilities": get_weight_for_sector("utilities"),
        }

        calculator = SectorPerformanceCalculator1D(volatility_multipliers)

        # Test with technology stocks (SOUN, BBAI)
        tech_symbols = ["SOUN", "BBAI"]
        print(f"\nTesting with technology stocks: {tech_symbols}")

        # Step 1: Retrieve real stock data
        tech_stock_data = []
        for symbol in tech_symbols:
            stock_data = await retrieval_service.get_1d_stock_data(symbol, "auto")
            if stock_data:
                stock_data.sector = "technology"  # Set sector for calculation
                tech_stock_data.append(stock_data)
                print(
                    f"  {symbol}: ${stock_data.current_price:.2f} "
                    f"(prev: ${stock_data.previous_close:.2f}, "
                    f"vol: {stock_data.current_volume:,})"
                )

        assert len(tech_stock_data) >= 1, "Should retrieve at least 1 tech stock"

        # Step 2: Calculate sector performance (need mock IWM data)
        iwm_current = 200.0  # Mock IWM current price
        iwm_previous = 198.0  # Mock IWM previous close

        # Calculate technology sector performance
        sector_result = calculator.calculate_sector_performance_1d(
            tech_stock_data, "technology", iwm_current, iwm_previous
        )

        print(f"\nTechnology Sector Results:")
        print(f"  Performance 1D: {sector_result.performance_1d:+.2f}%")
        print(f"  IWM Benchmark: {sector_result.iwm_benchmark:+.2f}%")
        print(f"  Alpha: {sector_result.alpha:+.2f}%")
        print(f"  Relative Strength: {sector_result.relative_strength}")
        print(f"  Stock Count: {sector_result.stock_count}")
        print(f"  Confidence: {sector_result.confidence:.2f}")
        print(f"  Calculation Time: {sector_result.calculation_time:.3f}s")

        # Validation
        assert sector_result.sector_name == "technology"
        assert sector_result.stock_count == len(tech_stock_data)
        assert sector_result.confidence > 0.0
        assert sector_result.calculation_time >= 0.0
        assert sector_result.relative_strength in [
            "STRONG_OUTPERFORM",
            "OUTPERFORM",
            "NEUTRAL",
            "UNDERPERFORM",
            "STRONG_UNDERPERFORM",
        ]

        print(f"\n✅ Complete 1D calculation pipeline test successful!")
        print("=" * 60)

        return sector_result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_stocks_different_apis(self):
        """Test calculation with stocks from different APIs"""
        retrieval_service = StockDataRetrieval1D()

        # Test getting data from different APIs
        test_results = {}

        for symbol in ["SOUN", "BBAI", "PATH"]:
            print(f"\nTesting {symbol} with different APIs:")

            # Test FMP
            fmp_data = await retrieval_service.get_1d_stock_data(symbol, "fmp")
            if fmp_data:
                test_results[f"{symbol}_fmp"] = fmp_data
                print(f"  FMP: ${fmp_data.current_price:.2f}")

            # Test Polygon
            polygon_data = await retrieval_service.get_1d_stock_data(symbol, "polygon")
            if polygon_data:
                test_results[f"{symbol}_polygon"] = polygon_data
                print(f"  Polygon: ${polygon_data.current_price:.2f}")

            # Test Auto (should pick best)
            auto_data = await retrieval_service.get_1d_stock_data(symbol, "auto")
            if auto_data:
                test_results[f"{symbol}_auto"] = auto_data
                print(f"  Auto: ${auto_data.current_price:.2f}")

        # Should have at least some successful retrievals
        assert (
            len(test_results) >= 3
        ), "Should successfully retrieve data from multiple sources"

        print(f"\n✅ Retrieved data from {len(test_results)} API calls")

        return test_results

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_edge_case_handling_with_real_data(self):
        """Test edge case handling with real market data"""
        retrieval_service = StockDataRetrieval1D()

        # Test with invalid symbol
        invalid_result = await retrieval_service.get_1d_stock_data(
            "INVALID_SYMBOL_XYZ", "auto"
        )
        assert invalid_result is None, "Should return None for invalid symbols"

        # Test with valid symbols but check for edge cases
        for symbol in ["SOUN", "BBAI"]:
            stock_data = await retrieval_service.get_1d_stock_data(symbol, "auto")
            if stock_data:
                # Validate data integrity
                assert (
                    stock_data.current_price > 0
                ), f"{symbol} should have positive current price"
                assert (
                    stock_data.previous_close > 0
                ), f"{symbol} should have positive previous close"
                assert (
                    stock_data.current_volume >= 0
                ), f"{symbol} should have non-negative volume"
                assert (
                    stock_data.avg_20_day_volume > 0
                ), f"{symbol} should have positive average volume"

                # Calculate performance change to check for extreme moves
                if stock_data.previous_close > 0:
                    change_pct = abs(
                        (stock_data.current_price - stock_data.previous_close)
                        / stock_data.previous_close
                        * 100
                    )
                    print(f"{symbol}: {change_pct:.2f}% daily change")

                    # Very extreme moves might indicate data issues (but don't fail the test)
                    if change_pct > 50:
                        print(
                            f"  WARNING: {symbol} has extreme price change: {change_pct:.2f}%"
                        )

        print("✅ Edge case handling test completed")


# Manual test runner
async def run_manual_integration_test():
    """Run integration test manually"""
    print("Starting 1D calculation integration test...")

    test_instance = Test1DCalculationWithRealData()

    try:
        # Test complete pipeline
        result1 = await test_instance.test_complete_1d_calculation_pipeline()

        # Test multiple API sources
        result2 = await test_instance.test_multiple_stocks_different_apis()

        # Test edge cases
        await test_instance.test_edge_case_handling_with_real_data()

        print("\n🎉 All integration tests passed! Step 1 + Step 2 working together!")

        return {"pipeline_result": result1, "api_test_results": result2}

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        raise


if __name__ == "__main__":
    # Allow manual execution
    asyncio.run(run_manual_integration_test())
