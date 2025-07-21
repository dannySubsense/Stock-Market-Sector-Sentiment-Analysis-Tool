"""
Integration Test for 1D API Comparison
Tests real FMP and Polygon APIs with the 5 specified test stocks
Run this manually to validate API data quality and determine primary data source
"""

import asyncio
import json
import pytest
from datetime import datetime
from services.stock_data_retrieval_1d import StockDataRetrieval1D


class TestAPIComparison1D:
    """Integration tests for API comparison with real market data"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_comparison_with_test_stocks(self):
        """
        Test both APIs with the 5 specified test stocks
        This is the primary integration test for Step 2
        """
        retrieval_service = StockDataRetrieval1D()

        # Run the comprehensive API test
        result = await retrieval_service.test_api_data_retrieval()

        # Print detailed results for analysis
        print("\n" + "=" * 80)
        print("API COMPARISON RESULTS")
        print("=" * 80)

        # Test summary
        summary = result["test_summary"]
        print(f"\nTest Summary:")
        print(f"  Symbols tested: {summary['symbols_tested']}")
        print(f"  Total symbols: {summary['total_symbols']}")
        print(f"  Successful tests: {summary['successful_tests']}")
        print(f"  Test timestamp: {summary['test_timestamp']}")

        # Performance analysis
        performance = result["performance_analysis"]
        print(f"\nPerformance Analysis:")
        print(f"  FMP:")
        print(
            f"    Average response time: {performance['fmp']['avg_response_time_ms']:.0f}ms"
        )
        print(
            f"    Max response time: {performance['fmp']['max_response_time_ms']:.0f}ms"
        )
        print(f"    Success rate: {performance['fmp']['success_rate']:.1f}%")
        print(f"  Polygon:")
        print(
            f"    Average response time: {performance['polygon']['avg_response_time_ms']:.0f}ms"
        )
        print(
            f"    Max response time: {performance['polygon']['max_response_time_ms']:.0f}ms"
        )
        print(f"    Success rate: {performance['polygon']['success_rate']:.1f}%")

        # Overall recommendation
        recommendation = result["overall_recommendation"]
        print(f"\nOverall Recommendation:")
        print(f"  Primary API: {recommendation['recommended_primary_api']}")
        print(f"  Confidence: {recommendation['confidence_percentage']:.1f}%")
        print(f"  Reasoning: {recommendation['recommendation_reasoning']}")

        # Individual stock results
        print(f"\nIndividual Stock Results:")
        for comparison in result["individual_comparisons"]:
            symbol = comparison["symbol"]
            print(f"\n  {symbol}:")
            print(f"    Recommended API: {comparison['recommended_api']}")
            print(f"    Reason: {comparison['recommendation_reason']}")
            print(f"    Data consistency: {comparison['data_consistency_score']:.2f}")

            # FMP results
            fmp = comparison["fmp_result"]
            print(
                f"    FMP: {'✓' if fmp['success'] else '✗'} | "
                f"{fmp['response_time_ms']:.0f}ms | "
                f"Quality: {fmp['data_quality_score']:.2f}"
            )
            if fmp["validation_issues"]:
                print(f"         Issues: {', '.join(fmp['validation_issues'])}")

            # Polygon results
            polygon = comparison["polygon_result"]
            print(
                f"    Polygon: {'✓' if polygon['success'] else '✗'} | "
                f"{polygon['response_time_ms']:.0f}ms | "
                f"Quality: {polygon['data_quality_score']:.2f}"
            )
            if polygon["validation_issues"]:
                print(f"             Issues: {', '.join(polygon['validation_issues'])}")

        print("\n" + "=" * 80)

        # Assertions for automated testing
        assert summary["total_symbols"] == 5, "Should test exactly 5 symbols"
        assert (
            summary["successful_tests"] >= 3
        ), "At least 3 symbols should have successful tests from both APIs"

        # At least one API should have decent performance
        assert (
            performance["fmp"]["success_rate"] >= 60
            or performance["polygon"]["success_rate"] >= 60
        ), "At least one API should have >60% success rate"

        # Recommendation should be made
        assert recommendation["recommended_primary_api"] in [
            "FMP",
            "Polygon",
        ], "Should recommend either FMP or Polygon"
        assert (
            recommendation["confidence_percentage"] > 0
        ), "Should have some confidence in recommendation"

        return result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_individual_stock_data_retrieval(self):
        """Test individual stock data retrieval for each test stock"""
        retrieval_service = StockDataRetrieval1D()
        test_stocks = ["SOUN", "BBAI", "PATH", "OCUL", "SMCI"]

        print("\n" + "=" * 60)
        print("INDIVIDUAL STOCK DATA RETRIEVAL TEST")
        print("=" * 60)

        for symbol in test_stocks:
            print(f"\nTesting {symbol}:")

            # Test auto mode (primary method)
            auto_result = await retrieval_service.get_1d_stock_data(symbol, "auto")
            if auto_result:
                print(f"  Auto mode: ✓")
                print(f"    Price: ${auto_result.current_price:.2f}")
                print(f"    Previous close: ${auto_result.previous_close:.2f}")
                print(f"    Volume: {auto_result.current_volume:,}")
                print(f"    Avg volume: {auto_result.avg_20_day_volume:,}")
                print(
                    f"    Change: {((auto_result.current_price - auto_result.previous_close) / auto_result.previous_close * 100):+.2f}%"
                )
            else:
                print(f"  Auto mode: ✗ (Failed to retrieve data)")

            # Test FMP specifically
            fmp_result = await retrieval_service.get_1d_stock_data(symbol, "fmp")
            print(f"  FMP mode: {'✓' if fmp_result else '✗'}")

            # Test Polygon specifically
            polygon_result = await retrieval_service.get_1d_stock_data(
                symbol, "polygon"
            )
            print(f"  Polygon mode: {'✓' if polygon_result else '✗'}")

            # At least one should work
            assert (
                auto_result or fmp_result or polygon_result
            ), f"At least one API should work for {symbol}"

        print("\n" + "=" * 60)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_data_validation_with_real_data(self):
        """Test data validation logic with real market data"""
        retrieval_service = StockDataRetrieval1D()

        print("\n" + "=" * 60)
        print("DATA VALIDATION TEST WITH REAL DATA")
        print("=" * 60)

        # Test with one stock to verify validation logic
        symbol = "SOUN"

        # Test FMP data validation
        fmp_result = await retrieval_service._test_fmp_api(symbol)
        if fmp_result.success:
            print(f"\nFMP data for {symbol}:")
            print(f"  Data quality score: {fmp_result.data_quality_score:.2f}")
            print(f"  Validation issues: {len(fmp_result.validation_issues)}")
            for issue in fmp_result.validation_issues:
                print(f"    - {issue}")

            # Verify data quality is reasonable
            assert (
                fmp_result.data_quality_score >= 0.5
            ), "FMP data quality should be at least 0.5"

        # Test Polygon data validation
        polygon_result = await retrieval_service._test_polygon_api(symbol)
        if polygon_result.success:
            print(f"\nPolygon data for {symbol}:")
            print(f"  Data quality score: {polygon_result.data_quality_score:.2f}")
            print(f"  Validation issues: {len(polygon_result.validation_issues)}")
            for issue in polygon_result.validation_issues:
                print(f"    - {issue}")

            # Verify data quality is reasonable
            assert (
                polygon_result.data_quality_score >= 0.5
            ), "Polygon data quality should be at least 0.5"

        print("\n" + "=" * 60)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_performance_benchmarking(self):
        """Benchmark API performance for 1D calculation scalability"""
        retrieval_service = StockDataRetrieval1D()
        test_symbols = ["SOUN", "BBAI", "PATH", "OCUL", "SMCI"] * 2  # 10 total requests

        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARKING TEST")
        print("=" * 60)

        # Time the overall operation
        start_time = asyncio.get_event_loop().time()

        # Test getting data for all symbols
        results = []
        for symbol in test_symbols:
            stock_data = await retrieval_service.get_1d_stock_data(symbol, "auto")
            results.append(stock_data is not None)

        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time

        success_rate = sum(results) / len(results) * 100
        avg_time_per_stock = total_time / len(test_symbols)

        print(f"\nPerformance Results:")
        print(f"  Total time: {total_time:.2f} seconds")
        print(f"  Average time per stock: {avg_time_per_stock:.3f} seconds")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Stocks tested: {len(test_symbols)}")

        # Performance expectations for 1D calculation
        assert (
            avg_time_per_stock < 2.0
        ), "Average time per stock should be under 2 seconds"
        assert success_rate >= 70, "Success rate should be at least 70%"

        # Extrapolate to full universe
        estimated_time_for_2000_stocks = avg_time_per_stock * 2000
        print(
            f"\nEstimated time for 2,000 stock universe: {estimated_time_for_2000_stocks:.0f} seconds ({estimated_time_for_2000_stocks/60:.1f} minutes)"
        )

        # Should be reasonable for 1D calculation requirements
        assert (
            estimated_time_for_2000_stocks < 300
        ), "Full universe should take less than 5 minutes"

        print("\n" + "=" * 60)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_save_comparison_results_for_documentation(self):
        """Save comprehensive test results for Step 2 documentation"""
        retrieval_service = StockDataRetrieval1D()

        # Run comprehensive test
        result = await retrieval_service.test_api_data_retrieval()

        # Save results to file for documentation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/integration/api_comparison_results_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"\nAPI comparison results saved to: {filename}")

        # Create summary for Step 2 completion
        summary = {
            "step_2_completion": {
                "timestamp": datetime.now().isoformat(),
                "test_stocks": retrieval_service.TEST_STOCKS,
                "recommended_api": result["overall_recommendation"][
                    "recommended_primary_api"
                ],
                "confidence": result["overall_recommendation"]["confidence_percentage"],
                "performance_summary": {
                    "fmp_avg_response_ms": result["performance_analysis"]["fmp"][
                        "avg_response_time_ms"
                    ],
                    "polygon_avg_response_ms": result["performance_analysis"][
                        "polygon"
                    ]["avg_response_time_ms"],
                    "fmp_success_rate": result["performance_analysis"]["fmp"][
                        "success_rate"
                    ],
                    "polygon_success_rate": result["performance_analysis"]["polygon"][
                        "success_rate"
                    ],
                },
                "data_quality_summary": {
                    "fmp_avg_quality": result["overall_recommendation"][
                        "quality_metrics"
                    ]["fmp_avg_data_quality"],
                    "polygon_avg_quality": result["overall_recommendation"][
                        "quality_metrics"
                    ]["polygon_avg_data_quality"],
                    "data_consistency": result["overall_recommendation"][
                        "quality_metrics"
                    ]["avg_data_consistency"],
                },
            }
        }

        summary_filename = f"tests/integration/step_2_summary_{timestamp}.json"
        with open(summary_filename, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"Step 2 summary saved to: {summary_filename}")

        return result


# Manual test runner for development
async def run_manual_api_test():
    """Run API comparison test manually for development"""
    print("Starting manual API comparison test...")

    test_instance = TestAPIComparison1D()

    try:
        # Run the main comparison test
        result = await test_instance.test_api_comparison_with_test_stocks()

        # Run individual stock test
        await test_instance.test_individual_stock_data_retrieval()

        # Run validation test
        await test_instance.test_data_validation_with_real_data()

        # Run performance test
        await test_instance.test_performance_benchmarking()

        # Save results
        await test_instance.test_save_comparison_results_for_documentation()

        print("\n✅ All API comparison tests completed successfully!")

        return result

    except Exception as e:
        print(f"\n❌ API comparison test failed: {e}")
        raise


if __name__ == "__main__":
    # Allow manual execution for development testing
    asyncio.run(run_manual_api_test())
