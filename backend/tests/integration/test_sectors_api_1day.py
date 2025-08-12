"""
Integration test for 1day sectors API endpoint
Tests against real database with actual data
"""

import pytest
from fastapi.testclient import TestClient
from main import app


class TestSectors1DayAPIIntegration:
    """Integration tests for 1day sectors API endpoint with real database"""

    def test_get_all_sectors_1day_integration(self):
        """Test GET /api/sectors/1day/ with real database"""
        with TestClient(app) as client:
            response = client.get("/api/sectors/1day/")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "sectors" in data
            assert "metadata" in data
            
            metadata = data["metadata"]
            assert "batch_id" in metadata
            assert "timestamp" in metadata
            assert "timeframe" in metadata
            assert metadata["timeframe"] == "1day"
            assert "is_stale" in metadata
            assert "sector_count" in metadata
            
            # Should have data (assuming database has been populated)
            sectors = data["sectors"]
            if sectors:  # Only test if we have data
                assert len(sectors) <= 11  # Should have at most 11 sectors
                
                # Check first sector structure
                first_sector = sectors[0]
                assert "sector" in first_sector
                assert "batch_id" in first_sector
                assert "sentiment_score" in first_sector
                assert "color_classification" in first_sector
                assert "trading_signal" in first_sector

    def test_get_sector_details_1day_integration(self):
        """Test GET /api/sectors/1day/{sector_name} with real database"""
        with TestClient(app) as client:
            # Test with a known sector
            response = client.get("/api/sectors/1day/technology")
            
            # Should either return data (200) or no data found (404)
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert "sector" in data
                assert "metadata" in data
                
                sector_data = data["sector"]
                assert sector_data["sector"] == "technology"
                assert "sentiment_score" in sector_data

    def test_freshness_status_1day_integration(self):
        """Test GET /api/sectors/1day/status/freshness with real database"""
        with TestClient(app) as client:
            response = client.get("/api/sectors/1day/status/freshness")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should have status information
            assert "status" in data
            assert "timeframe" in data
            assert data["timeframe"] == "1day"
            
            # Should have either data info or no_data status
            if data["status"] != "no_data":
                assert "is_stale" in data
                assert "age_minutes" in data
                assert "batch_id" in data 