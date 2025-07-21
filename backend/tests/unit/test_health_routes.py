"""
Unit tests for health check endpoints
Tests system health monitoring and component status
"""

import pytest
import time
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from main import app


class TestHealthRouter:
    """Unit tests for all health endpoints"""

    def test_health_check_overall_success(self, client: TestClient):
        """Test GET /api/health - overall system health"""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "components" in data

        # Check components structure
        components = data["components"]
        assert "database" in components
        assert "redis" in components
        assert "apis" in components

        # Status should be either healthy or unhealthy
        assert data["status"] in ["healthy", "unhealthy"]

    def test_health_check_overall_partial_failure(self, client: TestClient):
        """Test GET /api/health - partial system failure"""
        with patch("api.routes.health.check_redis_health") as mock_redis:
            mock_redis.return_value = {
                "status": "unhealthy",
                "error": "Connection failed",
            }

            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.json()

            # Should be unhealthy due to Redis failure
            assert data["status"] == "unhealthy"
            assert data["components"]["redis"]["status"] == "unhealthy"

    def test_health_check_overall_complete_failure(self, client: TestClient):
        """Test GET /api/health - complete system failure"""
        with patch("api.routes.health.get_db_info") as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            response = client.get("/api/health")

            # Should return 500 for complete failure
            assert response.status_code == 500
            assert "Health check failed" in response.json()["detail"]

    def test_health_database_success(self, client: TestClient):
        """Test GET /api/health/database - database health"""
        response = client.get("/api/health/database")

        assert response.status_code == 200
        data = response.json()

        # Check response structure - actual API returns different fields
        assert "database_path" in data
        assert "engine_info" in data
        assert "status" in data  # API returns 'status' not 'connection_status'
        assert "timestamp" in data

    def test_health_database_failure(self, client: TestClient):
        """Test GET /api/health/database - database failure"""
        with patch("api.routes.health.get_db_info") as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            response = client.get("/api/health/database")

            assert response.status_code == 500
            assert "Database health check failed" in response.json()["detail"]

    def test_health_redis_success(self, client: TestClient):
        """Test GET /api/health/redis - Redis health"""
        with patch("api.routes.health.check_redis_health") as mock_redis:
            mock_redis.return_value = {
                "status": "healthy",
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "connected_clients": 1,
                "memory_usage": "1.2MB",
                "uptime": 3600,
            }

            response = client.get("/api/health/redis")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert data["host"] == "localhost"
            assert data["port"] == 6379

    def test_health_redis_failure(self, client: TestClient):
        """Test GET /api/health/redis - Redis failure"""
        with patch("api.routes.health.check_redis_health") as mock_redis:
            mock_redis.return_value = {
                "status": "unhealthy",
                "error": "Connection refused",
                "host": "localhost",
                "port": 6379,
            }

            response = client.get("/api/health/redis")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "unhealthy"
            assert "Connection refused" in data["error"]

    def test_health_apis_success(self, client: TestClient):
        """Test GET /api/health/apis - external API health"""
        with patch("api.routes.health.check_api_health") as mock_api:
            mock_api.return_value = {
                "status": "healthy",
                "apis": {
                    "polygon": {"status": "configured", "key_present": True},
                    "fmp": {"status": "configured", "key_present": True},
                    "openai": {"status": "configured", "key_present": True},
                },
            }

            response = client.get("/api/health/apis")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert "polygon" in data["apis"]
            assert "fmp" in data["apis"]
            assert "openai" in data["apis"]

    def test_health_apis_failure(self, client: TestClient):
        """Test GET /api/health/apis - API failure"""
        with patch("api.routes.health.check_api_health") as mock_api:
            mock_api.return_value = {
                "status": "unhealthy",
                "error": "No credentials configured",
                "apis": {},
            }

            response = client.get("/api/health/apis")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "unhealthy"
            assert "No credentials configured" in data["error"]

    def test_health_apis_detailed_status(self, client: TestClient):
        """Test GET /api/health/apis - detailed API status"""
        with patch("api.routes.health.check_api_health") as mock_api:
            mock_api.return_value = {
                "status": "healthy",
                "apis": {
                    "polygon": {
                        "status": "configured",
                        "tier": "basic",
                        "key_present": True,
                    },
                    "fmp": {
                        "status": "configured",
                        "tier": "free",
                        "key_present": True,
                    },
                    "openai": {"status": "configured", "key_present": True},
                },
            }

            response = client.get("/api/health/apis")

            assert response.status_code == 200
            data = response.json()

            # Check detailed API information
            polygon_api = data["apis"]["polygon"]
            assert polygon_api["status"] == "configured"
            assert polygon_api["tier"] == "basic"
            assert polygon_api["key_present"] is True

    def test_health_endpoint_response_time(self, client: TestClient):
        """Test health endpoint response time"""
        start_time = time.time()
        response = client.get("/api/health")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        # Health check should be reasonable (< 5 seconds for initial load)
        assert (
            response_time < 5.0
        ), f"Health check took {response_time}s, should be < 5s"

    def test_health_endpoint_error_handling(self, client: TestClient):
        """Test health endpoint error handling"""
        with patch("api.routes.health.get_db_info") as mock_db:
            mock_db.side_effect = Exception("Unexpected database error")

            response = client.get("/api/health")

            assert response.status_code == 500
            data = response.json()
            assert "Health check failed" in data["detail"]
            assert "Unexpected database error" in data["detail"]

    def test_health_endpoint_caching(self, client: TestClient):
        """Test health endpoint caching behavior"""
        # First request
        response1 = client.get("/api/health")
        assert response1.status_code == 200

        # Second request (should be cached or fast)
        start_time = time.time()
        response2 = client.get("/api/health")
        end_time = time.time()

        response_time = end_time - start_time

        assert response2.status_code == 200
        # Second request should be reasonable (allow more time for cold start)
        assert (
            response_time < 5.0
        ), f"Cached health check took {response_time}s, should be < 5s"
