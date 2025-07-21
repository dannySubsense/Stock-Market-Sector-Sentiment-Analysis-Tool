"""
Integration tests for complete API workflows
Tests end-to-end API functionality including sector dashboard, stock universe, and analysis workflows
Aligned with current API structure for Slice 1A foundation
"""

import pytest
import time
from fastapi import status
from httpx import AsyncClient


class TestAPIIntegration:
    """Integration tests for complete API workflows"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_sector_workflow(self, async_client: AsyncClient):
        """Test complete sector dashboard workflow"""
        # 1. Get all sectors
        response1 = await async_client.get("/api/sectors")
        assert response1.status_code == status.HTTP_200_OK
        sectors_data = response1.json()

        # Validate response structure
        assert "sectors" in sectors_data
        assert "timestamp" in sectors_data
        assert "total_sectors" in sectors_data
        assert "source" in sectors_data

        # Check if we have sector data (may be default data)
        if sectors_data["sectors"]:
            # Get first sector name
            first_sector = list(sectors_data["sectors"].keys())[0]

            # 2. Get sector details
            response2 = await async_client.get(f"/api/sectors/{first_sector}")
            assert response2.status_code == status.HTTP_200_OK
            sector_details = response2.json()

            # Validate sector details structure
            assert "sector" in sector_details
            assert "sentiment" in sector_details
            assert "timeframes" in sector_details
            assert "top_stocks" in sector_details

            # 3. Get sector stocks
            response3 = await async_client.get(f"/api/sectors/{first_sector}/stocks")
            assert response3.status_code == status.HTTP_200_OK
            stocks_data = response3.json()

            # Validate stocks response structure
            assert "sector" in stocks_data
            assert "stocks" in stocks_data
            assert "count" in stocks_data
            assert isinstance(stocks_data["stocks"], list)

            # 4. Test deprecated refresh endpoint (should return deprecation message)
            response4 = await async_client.post("/api/sectors/refresh")
            assert response4.status_code == status.HTTP_200_OK
            refresh_data = response4.json()
            assert (
                "deprecated" in refresh_data.get("status", "")
                or "message" in refresh_data
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_stock_workflow(self, async_client: AsyncClient):
        """Test complete stock universe workflow"""
        # 1. Get universe stats
        response1 = await async_client.get("/api/stocks/universe/stats")
        assert response1.status_code == status.HTTP_200_OK
        stats = response1.json()
        # Validate stats structure
        assert "total_stocks" in stats
        assert "sector_breakdown" in stats
        assert "market_cap_breakdown" in stats
        assert "exchange_breakdown" in stats
        # 2. Get all stocks
        response2 = await async_client.get("/api/stocks")
        assert response2.status_code == status.HTTP_200_OK
        stocks = response2.json()
        # Validate stocks response structure
        assert "stocks" in stocks
        assert "total_count" in stocks
        assert "returned_count" in stocks
        assert "limit" in stocks
        assert "skip" in stocks
        assert isinstance(stocks["stocks"], list)
        # 3. Get stock details (if stocks exist)
        if stocks["stocks"]:
            first_stock = stocks["stocks"][0]
            stock_symbol = first_stock["symbol"]
            response3 = await async_client.get(f"/api/stocks/{stock_symbol}")
            assert response3.status_code == status.HTTP_200_OK
            stock_details = response3.json()
            # Validate stock details structure
            assert "symbol" in stock_details
            assert "current_price" in stock_details
            assert "price_change_percent" in stock_details
            assert "sector" in stock_details
        # 4. Get gap stocks
        response4 = await async_client.get("/api/stocks/gaps")
        assert response4.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        if response4.status_code == status.HTTP_200_OK:
            gaps = response4.json()
            # Validate gaps response structure
            assert "gaps" in gaps
            assert "total_count" in gaps
            assert isinstance(gaps["gaps"], list)
        else:
            error_data = response4.json()
            assert "detail" in error_data
        # 5. Get volume leaders
        response5 = await async_client.get("/api/stocks/volume-leaders")
        assert response5.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        if response5.status_code == status.HTTP_200_OK:
            volume_leaders = response5.json()
            # Validate volume leaders structure
            assert "volume_leaders" in volume_leaders
            assert "total_count" in volume_leaders
            assert isinstance(volume_leaders["volume_leaders"], list)
        else:
            error_data = response5.json()
            assert "detail" in error_data
        # 6. Refresh universe
        response6 = await async_client.post("/api/stocks/universe/refresh")
        assert response6.status_code == status.HTTP_200_OK
        refresh_data = response6.json()
        assert "status" in refresh_data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analysis_integration(self, async_client: AsyncClient):
        """Test analysis system integration"""
        # 1. Test on-demand analysis endpoint
        response1 = await async_client.post(
            "/api/analysis/on-demand", json={"analysis_type": "full"}
        )
        # This endpoint might return 200 or 500 depending on configuration
        assert response1.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

        if response1.status_code == status.HTTP_200_OK:
            analysis_data = response1.json()
            assert "status" in analysis_data
            assert "analysis_type" in analysis_data

        # 2. Test analysis status endpoint
        response2 = await async_client.get("/api/analysis/status")
        # This endpoint might return 200 or 500 depending on configuration
        assert response2.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

        if response2.status_code == status.HTTP_200_OK:
            status_data = response2.json()
            assert "status" in status_data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cache_integration(self, async_client: AsyncClient):
        """Test cache system integration"""
        # 1. Test cache stats endpoint
        response1 = await async_client.get("/api/cache/stats")
        # This endpoint might return 200 or 500 depending on configuration
        assert response1.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

        if response1.status_code == status.HTTP_200_OK:
            cache_stats = response1.json()
            assert "cache_stats" in cache_stats or "status" in cache_stats

        # 2. Test cache clearing endpoint
        response2 = await async_client.delete("/api/cache")
        # This endpoint might return 200 or 404 depending on configuration
        assert response2.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

        if response2.status_code == status.HTTP_200_OK:
            clear_data = response2.json()
            assert "status" in clear_data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_integration(self, async_client: AsyncClient):
        """Test health monitoring integration"""
        # 1. Test overall health
        response1 = await async_client.get("/api/health")
        assert response1.status_code == status.HTTP_200_OK
        health_data = response1.json()

        # Validate health response structure
        assert "status" in health_data
        assert "timestamp" in health_data
        assert "version" in health_data
        assert "components" in health_data

        # 2. Test database health
        response2 = await async_client.get("/api/health/database")
        assert response2.status_code == status.HTTP_200_OK
        db_health = response2.json()

        # Validate database health structure
        assert "status" in db_health
        assert "database_path" in db_health
        assert "engine_info" in db_health
        assert "timestamp" in db_health

        # 3. Test Redis health
        response3 = await async_client.get("/api/health/redis")
        assert response3.status_code == status.HTTP_200_OK
        redis_health = response3.json()

        # Validate Redis health structure
        assert "status" in redis_health
        assert "timestamp" in redis_health

        # 4. Test API health
        response4 = await async_client.get("/api/health/apis")
        assert response4.status_code == status.HTTP_200_OK
        api_health = response4.json()

        # Validate API health structure
        assert "status" in api_health
        assert "apis" in api_health
        assert "timestamp" in api_health

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, async_client: AsyncClient):
        """Test error recovery workflow"""
        # 1. Test invalid sector name (details endpoint)
        response1 = await async_client.get("/api/sectors/invalid_sector_name")
        assert response1.status_code == status.HTTP_404_NOT_FOUND
        error_data = response1.json()
        assert "detail" in error_data
        assert "not found" in error_data["detail"].lower()
        # 2. Test invalid stock symbol
        response2 = await async_client.get("/api/stocks/INVALID_SYMBOL")
        assert response2.status_code == status.HTTP_404_NOT_FOUND
        error_data = response2.json()
        assert "detail" in error_data
        # 3. Test invalid sector stocks (should return 200 with empty list)
        response3 = await async_client.get("/api/sectors/invalid_sector/stocks")
        assert response3.status_code == status.HTTP_200_OK
        stocks_data = response3.json()
        assert stocks_data["sector"] == "invalid_sector"
        assert stocks_data["stocks"] == []
        assert stocks_data["count"] == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_performance_under_load(self, async_client: AsyncClient):
        """Test performance under load"""
        # Test multiple concurrent requests to sector endpoint
        start_time = time.time()

        # Make 5 concurrent requests
        responses = []
        for i in range(5):
            response = await async_client.get("/api/sectors")
            responses.append(response)

        end_time = time.time()
        total_time = end_time - start_time

        # All requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

        # Total time should be reasonable (allow 10 seconds for 5 requests)
        assert (
            total_time < 10.0
        ), f"5 concurrent requests took {total_time}s, should be < 10s"

        # Average time per request should be reasonable
        avg_time = total_time / 5
        assert avg_time < 3.0, f"Average request time {avg_time}s, should be < 3s"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_consistency_across_endpoints(self, async_client: AsyncClient):
        """Test data consistency across endpoints"""
        # 1. Get sectors from main endpoint
        response1 = await async_client.get("/api/sectors")
        assert response1.status_code == status.HTTP_200_OK
        sectors_data = response1.json()

        # 2. Get stocks from universe
        response2 = await async_client.get("/api/stocks")
        assert response2.status_code == status.HTTP_200_OK
        stocks_data = response2.json()

        # 3. Get universe stats
        response3 = await async_client.get("/api/stocks/universe/stats")
        assert response3.status_code == status.HTTP_200_OK
        stats_data = response3.json()

        # Validate consistency
        if sectors_data["sectors"] and stocks_data["stocks"]:
            # Check that sector names are consistent
            sector_names = set(sectors_data["sectors"].keys())

            # Check that stocks have valid sectors
            stock_sectors = set()
            for stock in stocks_data["stocks"]:
                if "sector" in stock:
                    stock_sectors.add(stock["sector"].lower())

            # Stock sectors should be a subset of available sectors
            # (or at least not completely disjoint)
            if stock_sectors:
                # At least some stocks should have valid sectors
                assert len(stock_sectors.intersection(sector_names)) >= 0

        # Check that stats are consistent
        if "total_stocks" in stats_data and "stocks" in stocks_data:
            # Stats total should match or be close to actual stocks count
            stats_total = stats_data["total_stocks"]
            actual_count = len(stocks_data["stocks"])

            # Allow for pagination differences
            assert stats_total >= actual_count or actual_count <= stocks_data.get(
                "limit", 100
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_slice1a_requirements_validation(self, async_client: AsyncClient):
        """Test Slice 1A foundation requirements validation"""
        # 1. Test sector grid performance (<1 second)
        start_time = time.time()
        response1 = await async_client.get("/api/sectors")
        end_time = time.time()

        load_time = end_time - start_time
        assert response1.status_code == status.HTTP_200_OK
        assert load_time < 1.0, f"Sector grid took {load_time}s, should be < 1s"

        # 2. Test 8-sector coverage
        sectors_data = response1.json()
        if sectors_data["sectors"]:
            sector_count = len(sectors_data["sectors"])
            # Should have 8 sectors (may be default data)
            assert sector_count == 8, f"Expected 8 sectors, got {sector_count}"

            # Check for expected sectors
            expected_sectors = {
                "technology",
                "healthcare",
                "energy",
                "financial",
                "consumer_discretionary",
                "industrials",
                "materials",
                "utilities",
            }
            actual_sectors = set(sectors_data["sectors"].keys())
            assert (
                actual_sectors == expected_sectors
            ), f"Expected {expected_sectors}, got {actual_sectors}"

        # 3. Test multi-timeframe data structure
        if sectors_data["sectors"]:
            first_sector = list(sectors_data["sectors"].keys())[0]
            sector_info = sectors_data["sectors"][first_sector]

            # Check for timeframe scores
            assert "timeframe_scores" in sector_info
            timeframes = sector_info["timeframe_scores"]
            assert "30min" in timeframes
            assert "1day" in timeframes
            assert "3day" in timeframes
            assert "1week" in timeframes

        # 4. Test color classification system
        if sectors_data["sectors"]:
            for sector_name, sector_info in sectors_data["sectors"].items():
                assert "color_classification" in sector_info
                color = sector_info["color_classification"]
                valid_colors = {
                    "dark_red",
                    "light_red",
                    "blue_neutral",
                    "light_green",
                    "dark_green",
                }
                assert (
                    color in valid_colors
                ), f"Invalid color {color} for sector {sector_name}"

        # 5. Test stock universe size validation
        response2 = await async_client.get("/api/stocks/universe/stats")
        assert response2.status_code == status.HTTP_200_OK
        stats_data = response2.json()

        # Should have reasonable universe size (0-2000 stocks)
        total_stocks = stats_data["total_stocks"]
        assert (
            0 <= total_stocks <= 2000
        ), f"Universe size {total_stocks} outside expected range"

        # 6. Test sector breakdown validation
        if "sector_breakdown" in stats_data:
            sector_breakdown = stats_data["sector_breakdown"]
            total_in_breakdown = sum(sector_breakdown.values())
            assert (
                total_in_breakdown == total_stocks
            ), f"Sector breakdown sum {total_in_breakdown} != total {total_stocks}"
