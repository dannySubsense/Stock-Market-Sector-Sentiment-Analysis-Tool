"""
Simple E2E Test for Market Sector Sentiment Analysis Tool
Basic test to verify E2E test suite functionality
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestSimpleE2E:
    """
    Simple E2E test to verify test suite functionality
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_simple_health_check(self, async_client: AsyncClient):
        """
        Simple E2E test: Basic health check

        This test verifies that:
        1. The E2E test suite is working
        2. The async client is functional
        3. The health endpoint is accessible
        """
        # Test health endpoint
        response = await async_client.get("/api/health")
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Health check failed: {response.status_code}"

        # Verify response structure
        health_data = response.json()
        assert "status" in health_data, "Health response missing 'status' key"
        assert "timestamp" in health_data, "Health response missing 'timestamp' key"
        assert "version" in health_data, "Health response missing 'version' key"

        print("✅ Simple E2E test passed - health endpoint is working")

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_simple_sectors_endpoint(self, async_client: AsyncClient):
        """
        Simple E2E test: Sectors endpoint

        This test verifies that:
        1. The sectors endpoint is accessible
        2. The response structure is correct
        3. Basic data validation works
        """
        # Test sectors endpoint
        response = await async_client.get("/api/sectors")
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Sectors endpoint failed: {response.status_code}"

        # Verify response structure
        sectors_data = response.json()
        assert "sectors" in sectors_data, "Sectors response missing 'sectors' key"
        assert "timestamp" in sectors_data, "Sectors response missing 'timestamp' key"
        assert (
            "total_sectors" in sectors_data
        ), "Sectors response missing 'total_sectors' key"

        print("✅ Simple E2E test passed - sectors endpoint is working")

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_simple_stocks_endpoint(self, async_client: AsyncClient):
        """
        Simple E2E test: Stocks endpoint

        This test verifies that:
        1. The stocks endpoint is accessible
        2. The response structure is correct
        3. Basic data validation works
        """
        # Test stocks endpoint
        response = await async_client.get("/api/stocks")
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Stocks endpoint failed: {response.status_code}"

        # Verify response structure
        stocks_data = response.json()
        assert "stocks" in stocks_data, "Stocks response missing 'stocks' key"
        assert "total_count" in stocks_data, "Stocks response missing 'total_count' key"
        assert (
            "returned_count" in stocks_data
        ), "Stocks response missing 'returned_count' key"

        print("✅ Simple E2E test passed - stocks endpoint is working")
