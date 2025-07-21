"""
Integration tests for FMP Client - Phase 1: Stock Screener Complete
Tests the new unlimited stock screener method with real FMP API
"""

import pytest
import asyncio
from typing import Dict, Any
import logging

from mcp.fmp_client import get_fmp_client, test_fmp_connection

logger = logging.getLogger(__name__)


class TestFMPStockScreenerIntegration:
    """Integration tests for FMP stock screener complete method"""

    @pytest.mark.asyncio
    async def test_fmp_connection(self):
        """Test basic FMP API connection"""
        result = await test_fmp_connection()

        # Log result for debugging
        logger.info(f"FMP connection test result: {result}")

        # Should either succeed or fail gracefully
        assert result["status"] in ["success", "error"]
        assert "message" in result

        if result["status"] == "error":
            pytest.skip(f"FMP API not available: {result['message']}")

    @pytest.mark.asyncio
    async def test_get_stock_screener_complete_integration(self):
        """Test complete stock screener with real FMP API"""
        client = get_fmp_client()

        # Test connection first
        connection_result = await client.test_connection()
        if connection_result["status"] != "success":
            pytest.skip(
                f"FMP API not available: {connection_result.get('message', 'Unknown error')}"
            )

        # Call the new complete screener method
        result = await client.get_stock_screener_complete()

        # Log result for analysis
        logger.info(f"Stock screener result status: {result['status']}")
        logger.info(f"Universe size: {result.get('universe_size', 0)}")

        # Verify response structure
        assert "status" in result
        assert "universe_size" in result
        assert "stocks" in result
        assert "processing_timestamp" in result

        if result["status"] == "success":
            # Verify we got reasonable data
            universe_size = result["universe_size"]
            stocks = result["stocks"]

            logger.info(f"Successfully retrieved {universe_size} stocks")

            # Should get reasonable number of stocks (our target is ~1,200-1,500)
            assert universe_size >= 0  # At minimum should not error
            assert len(stocks) == universe_size
            assert isinstance(stocks, list)

            # Verify criteria are properly set
            assert "criteria" in result
            criteria = result["criteria"]
            assert criteria["market_cap_range"] == "$10M - $2B"
            assert criteria["price_range"] == "$1.00 - $100.00"
            assert criteria["min_volume"] == "1M+ daily"
            assert criteria["exchanges"] == "NASDAQ, NYSE"
            assert criteria["active_only"] is True

            # Verify filters were applied correctly
            assert "filters_applied" in result
            filters = result["filters_applied"]
            assert filters["marketCapMoreThan"] == "10000000"
            assert filters["marketCapLowerThan"] == "2000000000"
            assert filters["exchange"] == "NASDAQ,NYSE"
            assert filters["volumeMoreThan"] == "1000000"
            assert "limit" not in filters  # CRITICAL: No limit parameter

            # If we got stocks, verify their structure
            if universe_size > 0:
                sample_stock = stocks[0]
                required_fields = [
                    "symbol",
                    "companyName",
                    "marketCap",
                    "price",
                    "exchange",
                ]
                for field in required_fields:
                    assert field in sample_stock, f"Missing required field: {field}"

                # Log sample for verification
                logger.info(f"Sample stock: {sample_stock}")

                # Verify the stock meets our criteria (basic validation)
                market_cap = sample_stock.get("marketCap", 0)
                price = sample_stock.get("price", 0)
                exchange = sample_stock.get("exchange", "")

                # These should meet our criteria if FMP filtering worked
                if market_cap > 0:
                    assert (
                        10_000_000 <= market_cap <= 2_000_000_000
                    ), f"Market cap {market_cap} outside range"
                if price > 0:
                    assert 1.00 <= price <= 100.00, f"Price {price} outside range"
                if exchange:
                    assert exchange in [
                        "NASDAQ",
                        "NYSE",
                    ], f"Invalid exchange: {exchange}"

            # Success metrics from our plan
            if universe_size >= 1200:
                logger.info("✅ SUCCESS: Universe size meets target (1,200+ stocks)")
            elif universe_size >= 500:
                logger.info(
                    "⚠️  PARTIAL: Reasonable universe size, may need criteria adjustment"
                )
            else:
                logger.warning(
                    f"⚠️  LOW: Universe size {universe_size} below expectations"
                )

        else:
            # Handle API errors gracefully
            error_msg = result.get("message", "Unknown error")
            logger.error(f"FMP stock screener failed: {error_msg}")

            # For rate limiting, this is expected on free tier
            if "429" in error_msg or "rate" in error_msg.lower():
                pytest.skip("FMP rate limited - expected on free tier")
            else:
                # Other errors should be investigated
                pytest.fail(f"Unexpected FMP API error: {error_msg}")

    @pytest.mark.asyncio
    async def test_universe_data_quality(self):
        """Test data quality of retrieved universe"""
        client = get_fmp_client()

        # Test connection first
        connection_result = await client.test_connection()
        if connection_result["status"] != "success":
            pytest.skip(
                f"FMP API not available: {connection_result.get('message', 'Unknown error')}"
            )

        result = await client.get_stock_screener_complete()

        if result["status"] != "success":
            pytest.skip(
                f"FMP screener failed: {result.get('message', 'Unknown error')}"
            )

        stocks = result["stocks"]
        universe_size = result["universe_size"]

        if universe_size == 0:
            pytest.skip("No stocks returned - cannot test data quality")

        # Data quality checks
        symbols_with_data = 0
        sectors_found = set()
        exchanges_found = set()

        for stock in stocks[:100]:  # Check first 100 for performance
            symbol = stock.get("symbol", "")
            sector = stock.get("sector", "")
            exchange = stock.get("exchange", "")

            if symbol:
                symbols_with_data += 1
            if sector:
                sectors_found.add(sector.lower())
            if exchange:
                exchanges_found.add(exchange)

        # Quality metrics
        data_completeness = symbols_with_data / min(100, universe_size) * 100
        logger.info(f"Data completeness: {data_completeness:.1f}%")
        logger.info(f"Sectors found: {sorted(sectors_found)}")
        logger.info(f"Exchanges found: {sorted(exchanges_found)}")

        # Assertions for data quality
        assert (
            data_completeness >= 90
        ), f"Low data completeness: {data_completeness:.1f}%"
        assert len(sectors_found) >= 3, f"Too few sectors found: {len(sectors_found)}"

        # Should include our target exchanges
        expected_exchanges = {"NASDAQ", "NYSE"}
        found_exchanges = {ex.upper() for ex in exchanges_found}
        assert expected_exchanges.intersection(
            found_exchanges
        ), f"Missing target exchanges in {found_exchanges}"


class TestFMPPerformanceMetrics:
    """Test performance metrics for FMP integration"""

    @pytest.mark.asyncio
    async def test_response_time(self):
        """Test that FMP response time meets <30 second target"""
        import time

        client = get_fmp_client()

        # Test connection first
        connection_result = await client.test_connection()
        if connection_result["status"] != "success":
            pytest.skip(
                f"FMP API not available: {connection_result.get('message', 'Unknown error')}"
            )

        # Measure response time
        start_time = time.time()
        result = await client.get_stock_screener_complete()
        end_time = time.time()

        response_time = end_time - start_time
        logger.info(f"FMP screener response time: {response_time:.2f} seconds")

        if result["status"] == "success":
            # Our target is <30 seconds from the plan
            assert (
                response_time < 30
            ), f"Response time {response_time:.2f}s exceeds 30s target"

            if response_time < 10:
                logger.info("✅ EXCELLENT: Response time under 10 seconds")
            elif response_time < 30:
                logger.info("✅ GOOD: Response time meets 30 second target")
        else:
            logger.info(
                f"API call failed in {response_time:.2f}s: {result.get('message', 'Unknown error')}"
            )

    @pytest.mark.asyncio
    async def test_api_call_efficiency(self):
        """Verify single API call approach vs previous multi-call approach"""
        client = get_fmp_client()

        connection_result = await client.test_connection()
        if connection_result["status"] != "success":
            pytest.skip(
                f"FMP API not available: {connection_result.get('message', 'Unknown error')}"
            )

        # Track number of API calls (should be exactly 1)
        call_count = 0
        original_get = client.client.get

        async def counting_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return await original_get(*args, **kwargs)

        client.client.get = counting_get

        result = await client.get_stock_screener_complete()

        # Restore original method
        client.client.get = original_get

        logger.info(f"API calls made: {call_count}")

        # Should be exactly 1 call (99.97% reduction from 3,000+ calls)
        assert call_count == 1, f"Expected 1 API call, made {call_count}"

        if result["status"] == "success":
            universe_size = result["universe_size"]
            logger.info(
                f"✅ SUCCESS: Retrieved {universe_size} stocks with single API call"
            )
            logger.info("✅ 99.97% reduction in API calls achieved (3,000+ → 1)")
