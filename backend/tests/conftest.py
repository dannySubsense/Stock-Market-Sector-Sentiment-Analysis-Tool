"""
Pytest configuration and fixtures for Market Sector Sentiment Analysis Tool
Provides test database, mock APIs, and common test utilities
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from core.database import get_db
from core.config import get_settings
import pytest_asyncio

# Import E2E fixtures to make them available to all tests
try:
    from .e2e.conftest_e2e import (
        e2e_test_data,
        e2e_test_environment,
        e2e_workflow_steps,
        e2e_performance_benchmarks,
        e2e_api_chains,
        e2e_data_flows,
        e2e_performance_targets,
        e2e_error_scenarios,
        e2e_benchmark_targets,
        e2e_system_targets
    )
except ImportError:
    # E2E fixtures not available, create empty fixtures
    @pytest.fixture
    def e2e_test_data():
        return {}
    
    @pytest.fixture
    def e2e_test_environment():
        return {}
    
    @pytest.fixture
    def e2e_workflow_steps():
        return {}
    
    @pytest.fixture
    def e2e_performance_benchmarks():
        return {}
    
    @pytest.fixture
    def e2e_api_chains():
        return {}
    
    @pytest.fixture
    def e2e_data_flows():
        return {}
    
    @pytest.fixture
    def e2e_performance_targets():
        return {}
    
    @pytest.fixture
    def e2e_error_scenarios():
        return {}
    
    @pytest.fixture
    def e2e_benchmark_targets():
        return {}
    
    @pytest.fixture
    def e2e_system_targets():
        return {}


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_polygon_api():
    """Mock Polygon.io API responses for testing."""
    mock = AsyncMock()
    
    # Mock ticker data
    mock.get_all_tickers.return_value = [
        {
            "ticker": "SOUN",
            "name": "SoundHound AI Inc",
            "market_cap": 180_000_000,
            "volume": 2_100_000,
            "price": 5.20,
            "sector": "Technology"
        },
        {
            "ticker": "BBAI", 
            "name": "BigBear.ai Holdings Inc",
            "market_cap": 120_000_000,
            "volume": 950_000,
            "price": 3.80,
            "sector": "Technology"
        },
        {
            "ticker": "OCUL",
            "name": "Ocular Therapeutix Inc",
            "market_cap": 450_000_000,
            "volume": 1_800_000,
            "price": 4.10,
            "sector": "Healthcare"
        }
    ]
    
    # Mock sector performance data
    mock.get_sector_performance.return_value = {
        "technology": {
            "performance_30min": -0.8,
            "performance_1day": -2.4,
            "performance_3day": -5.1,
            "performance_1week": 1.2,
            "sentiment_score": -0.73,
            "color_code": "DARK_RED"
        },
        "healthcare": {
            "performance_30min": 0.6,
            "performance_1day": 1.2,
            "performance_3day": 2.1,
            "performance_1week": 3.5,
            "sentiment_score": 0.58,
            "color_code": "DARK_GREEN"
        }
    }
    
    return mock


@pytest.fixture
def mock_fmp_api():
    """Mock FMP API responses for testing."""
    mock = AsyncMock()
    
    # Mock stock list
    mock.get_stock_list.return_value = [
        {"symbol": "SOUN", "name": "SoundHound AI Inc", "exchange": "NASDAQ"},
        {"symbol": "BBAI", "name": "BigBear.ai Holdings Inc", "exchange": "NASDAQ"},
        {"symbol": "OCUL", "name": "Ocular Therapeutix Inc", "exchange": "NASDAQ"}
    ]
    
    # Mock company profiles
    mock.get_company_profile.return_value = {
        "symbol": "SOUN",
        "companyName": "SoundHound AI Inc",
        "sector": "Technology",
        "marketCap": 180_000_000,
        "price": 5.20,
        "volume": 2_100_000
    }
    
    return mock


@pytest.fixture
def test_sectors_data():
    """Sample sector data for testing."""
    return [
        {
            "sector": "technology",
            "sentiment_score": -0.73,
            "color_code": "DARK_RED",
            "performance_30min": -0.8,
            "performance_1day": -2.4,
            "performance_3day": -5.1,
            "performance_1week": 1.2,
            "top_bullish": ["SMCI", "PATH", "NVDA"],
            "top_bearish": ["SOUN", "BBAI", "PATH"]
        },
        {
            "sector": "healthcare",
            "sentiment_score": 0.58,
            "color_code": "DARK_GREEN", 
            "performance_30min": 0.6,
            "performance_1day": 1.2,
            "performance_3day": 2.1,
            "performance_1week": 3.5,
            "top_bullish": ["OCUL", "KPTI", "DTIL"],
            "top_bearish": []
        }
    ]


@pytest.fixture
def test_stocks_data():
    """Sample stock data for testing."""
    return [
        {
            "symbol": "SOUN",
            "name": "SoundHound AI Inc",
            "sector": "Technology",
            "market_cap": 180_000_000,
            "price": 5.20,
            "volume": 2_100_000,
            "avg_volume": 1_800_000,
            "price_change": -0.082,
            "volume_ratio": 1.17
        },
        {
            "symbol": "BBAI",
            "name": "BigBear.ai Holdings Inc", 
            "sector": "Technology",
            "market_cap": 120_000_000,
            "price": 3.80,
            "volume": 950_000,
            "avg_volume": 1_200_000,
            "price_change": -0.061,
            "volume_ratio": 0.79
        },
        {
            "symbol": "OCUL",
            "name": "Ocular Therapeutix Inc",
            "sector": "Healthcare", 
            "market_cap": 450_000_000,
            "price": 4.10,
            "volume": 1_800_000,
            "avg_volume": 1_500_000,
            "price_change": 0.45,
            "volume_ratio": 1.20
        }
    ]


@pytest.fixture
def mock_redis():
    """Mock Redis cache for testing."""
    mock = Mock()
    mock.get.return_value = None  # Default to cache miss
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = False
    mock.ttl.return_value = -1
    return mock


@pytest.fixture
def mock_database():
    """Mock database session for testing."""
    mock = Mock()
    mock.query.return_value = mock
    mock.filter.return_value = mock
    mock.all.return_value = []
    mock.first.return_value = None
    mock.count.return_value = 0
    mock.add.return_value = None
    mock.commit.return_value = None
    mock.rollback.return_value = None
    return mock


# Test markers for pytest
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slice1a: mark test as Slice 1A specific"
    )
    config.addinivalue_line(
        "markers", "slice1b: mark test as Slice 1B specific"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "external_apis: mark test as requiring external APIs"
    ) 