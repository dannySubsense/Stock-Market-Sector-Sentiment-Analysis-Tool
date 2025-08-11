"""
Pytest configuration and fixtures for Market Sector Sentiment Analysis Tool
Provides test database, mock APIs, and common test utilities
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, MagicMock
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

# Import service dependencies for mocking
import os
ANALYSIS_ENABLED: bool = os.getenv("ANALYSIS_ENABLED", "0") == "1"

if ANALYSIS_ENABLED:
    from services.cache_service import get_cache_service
    from services.analysis_scheduler import get_analysis_scheduler
    from services.sector_calculator import get_sector_calculator
    from services.stock_ranker import get_stock_ranker
    from services.theme_detection import get_theme_detector
    from services.temperature_monitor import get_temperature_monitor
    from services.sympathy_network import get_sympathy_network
    from services.performance_monitor import get_performance_monitor
else:
    async def get_cache_service():
        class _Disabled:
            async def get_statistics(self):
                return {}
            async def clear_all(self):
                return None
        return _Disabled()

    def get_analysis_scheduler():
        class _Disabled:
            def get_status(self):
                return {"status": "disabled"}
        return _Disabled()

    def get_sector_calculator():
        class _Disabled:
            pass
        return _Disabled()

    def get_stock_ranker():
        class _Disabled:
            pass
        return _Disabled()

    def get_theme_detector():
        class _Disabled:
            pass
        return _Disabled()

    def get_temperature_monitor():
        class _Disabled:
            pass
        return _Disabled()

    def get_sympathy_network():
        class _Disabled:
            pass
        return _Disabled()

    async def get_performance_monitor():
        class _Disabled:
            async def get_cache_performance(self):
                return {}
        return _Disabled()
from services.data_freshness_service import get_freshness_service

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
        e2e_system_targets,
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


# Add mock database session fixture
@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing"""
    mock_session = MagicMock()

    # Create simple mock sector object (not Mock() to avoid recursion)
    class MockSector:
        def __init__(self):
            self.sector = "technology"
            self.sentiment_score = 0.15
            self.color_classification = "bullish"
            self.confidence_level = 0.85
            self.timeframe_30min = 0.12
            self.timeframe_1day = 0.15
            self.timeframe_3day = 0.18
            self.timeframe_1week = 0.20
            self.top_bullish_stocks = ["AAPL", "MSFT", "GOOGL"]
            self.top_bearish_stocks = ["TSLA", "META", "AMZN"]
            # Additional properties the route expects
            self.trading_signal = "bullish"
            self.sentiment_description = "Technology sector showing positive momentum"
            self.last_updated = None
            self.is_stale = False

        def get_timeframe_summary(self):
            return {
                "30min": self.timeframe_30min,
                "1day": self.timeframe_1day,
                "3day": self.timeframe_3day,
                "1week": self.timeframe_1week,
            }

    mock_sector = MockSector()

    # Mock query behavior to return sector data for "technology" and None for others
    def mock_query_filter_first(*args, **kwargs):
        # Check if this is querying for "technology" sector
        return mock_sector

    # Return empty list for top_stocks query to avoid stock processing
    mock_session.query.return_value.filter.return_value.all.return_value = []
    mock_session.query.return_value.filter.return_value.first.side_effect = (
        mock_query_filter_first
    )
    mock_session.query.return_value.filter.return_value.count.return_value = 0
    mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = (
        []
    )
    mock_session.commit.return_value = None
    mock_session.add.return_value = None
    mock_session.rollback.return_value = None
    return mock_session


# Add mock service fixtures (sync fixtures that return AsyncMock objects)
@pytest.fixture
def mock_cache_service():
    """Create a mock cache service"""
    mock_service = AsyncMock()
    mock_service.get_sectors.return_value = {
        "sectors": {
            "technology": {
                "sector": "technology",
                "sentiment_score": 0.15,
                "color_classification": "bullish",
                "timeframe_scores": {
                    "30min": 0.12,
                    "1day": 0.15,
                    "3day": 0.18,
                    "1week": 0.20,
                },
                "top_bullish": ["AAPL", "MSFT", "GOOGL"],
                "top_bearish": ["TSLA", "META", "AMZN"],
            }
        }
    }
    mock_service.get_statistics.return_value = {
        "hit_rate": 0.85,
        "miss_rate": 0.15,
        "total_requests": 100,
        "cache_size": 50,
    }
    return mock_service


@pytest.fixture
def mock_analysis_scheduler():
    """Create a mock analysis scheduler"""
    mock_scheduler = AsyncMock()
    mock_scheduler.get_analysis_status.return_value = {
        "current_analysis": None,
        "last_completed": None,
        "status": "idle",
    }
    mock_scheduler.run_comprehensive_daily_analysis.return_value = {
        "status": "success",
        "analysis_type": "comprehensive_daily",
    }
    mock_scheduler.run_on_demand_analysis.return_value = {
        "status": "success",
        "analysis_type": "on_demand",
    }
    return mock_scheduler


@pytest.fixture
def mock_sector_calculator():
    """Create a mock sector calculator"""
    mock_calculator = AsyncMock()
    mock_calculator.calculate_all_sectors.return_value = {
        "status": "success",
        "sectors": {"technology": {"sentiment_score": 0.15}},
    }
    return mock_calculator


@pytest.fixture
def mock_stock_ranker():
    """Create a mock stock ranker"""
    mock_ranker = AsyncMock()
    mock_ranker.rank_all_sectors.return_value = {
        "status": "success",
        "rankings": {"technology": ["AAPL", "MSFT", "GOOGL"]},
    }
    return mock_ranker


@pytest.fixture
def mock_theme_detector():
    """Create a mock theme detector"""
    mock_detector = AsyncMock()
    mock_detector.scan_for_themes.return_value = {"status": "success", "themes": []}
    return mock_detector


@pytest.fixture
def mock_temperature_monitor():
    """Create a mock temperature monitor"""
    mock_monitor = AsyncMock()
    mock_monitor.start_monitoring.return_value = None
    mock_monitor.get_current_temperature.return_value = {"temperature": 0.5}
    return mock_monitor


@pytest.fixture
def mock_sympathy_network():
    """Create a mock sympathy network"""
    mock_network = AsyncMock()
    mock_network.get_network_for_symbol.return_value = {
        "correlated_stocks": [],
        "confidence": 0.0,
    }
    return mock_network


@pytest.fixture
def mock_performance_monitor():
    """Create a mock performance monitor"""
    mock_monitor = AsyncMock()
    mock_monitor.get_cache_performance.return_value = {
        "avg_response_time": 0.1,
        "cache_hit_ratio": 0.85,
    }
    return mock_monitor


@pytest.fixture
def mock_freshness_service():
    """Create a mock data freshness service"""
    mock_service = Mock()
    
    # Create mock sector sentiment records
    from models.sector_sentiment import SectorSentiment
    from datetime import datetime, timezone
    
    # Create 11 mock sector records for a complete batch
    sectors = ["basic_materials", "communication_services", "consumer_cyclical", 
               "consumer_defensive", "energy", "financial_services", "healthcare",
               "industrials", "real_estate", "technology", "utilities"]
    
    batch_id = "test_batch_123"
    timestamp = datetime.now(timezone.utc)
    
    mock_records = []
    for sector in sectors:
        mock_record = Mock(spec=SectorSentiment)
        mock_record.sector = sector
        mock_record.timeframe = "1day"
        mock_record.timestamp = timestamp
        mock_record.batch_id = batch_id
        mock_record.sentiment_score = 0.15
        mock_record.bullish_count = 5
        mock_record.bearish_count = 3
        mock_record.total_volume = 1000000
        mock_record.created_at = timestamp
        
        # Add to_dict method
        mock_record.to_dict.return_value = {
            "sector": sector,
            "timeframe": "1day", 
            "timestamp": timestamp.isoformat(),
            "batch_id": batch_id,
            "sentiment_score": 0.15,
            "color_classification": "blue_neutral",
            "trading_signal": "neutral",
            "bullish_count": 5,
            "bearish_count": 3,
            "total_volume": 1000000,
            "created_at": timestamp.isoformat()
        }
        mock_records.append(mock_record)
    
    # Mock get_latest_complete_batch to return our mock records
    mock_service.get_latest_complete_batch.return_value = (mock_records, False)  # False = not stale
    
    # Mock other methods
    mock_service.validate_batch_integrity.return_value = {"valid": True, "issues": []}
    mock_service.get_batch_age_info.return_value = {"age_minutes": 30.0}
    
    return mock_service


# Update the client fixture to use dependency overrides
@pytest.fixture
def client(
    mock_db_session,
    mock_cache_service,
    mock_analysis_scheduler,
    mock_sector_calculator,
    mock_stock_ranker,
    mock_theme_detector,
    mock_temperature_monitor,
    mock_sympathy_network,
    mock_performance_monitor,
    mock_freshness_service,
) -> Generator:
    """Create a test client with mocked dependencies."""

    # Override all service dependencies
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
    app.dependency_overrides[get_analysis_scheduler] = lambda: mock_analysis_scheduler
    app.dependency_overrides[get_sector_calculator] = lambda: mock_sector_calculator
    app.dependency_overrides[get_stock_ranker] = lambda: mock_stock_ranker
    app.dependency_overrides[get_theme_detector] = lambda: mock_theme_detector
    app.dependency_overrides[get_temperature_monitor] = lambda: mock_temperature_monitor
    app.dependency_overrides[get_sympathy_network] = lambda: mock_sympathy_network
    app.dependency_overrides[get_performance_monitor] = lambda: mock_performance_monitor
    app.dependency_overrides[get_freshness_service] = lambda: mock_freshness_service

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Clear overrides after test
        app.dependency_overrides.clear()


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
            "sector": "Technology",
        },
        {
            "ticker": "BBAI",
            "name": "BigBear.ai Holdings Inc",
            "market_cap": 120_000_000,
            "volume": 950_000,
            "price": 3.80,
            "sector": "Technology",
        },
        {
            "ticker": "OCUL",
            "name": "Ocular Therapeutix Inc",
            "market_cap": 450_000_000,
            "volume": 1_800_000,
            "price": 4.10,
            "sector": "Healthcare",
        },
    ]

    # Mock sector performance data
    mock.get_sector_performance.return_value = {
        "technology": {
            "performance_30min": -0.8,
            "performance_1day": -2.4,
            "performance_3day": -5.1,
            "performance_1week": 1.2,
            "sentiment_score": -0.73,
            "color_code": "DARK_RED",
        },
        "healthcare": {
            "performance_30min": 0.6,
            "performance_1day": 1.2,
            "performance_3day": 2.1,
            "performance_1week": 3.5,
            "sentiment_score": 0.58,
            "color_code": "DARK_GREEN",
        },
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
        {"symbol": "OCUL", "name": "Ocular Therapeutix Inc", "exchange": "NASDAQ"},
    ]

    # Mock company profiles
    mock.get_company_profile.return_value = {
        "symbol": "SOUN",
        "companyName": "SoundHound AI Inc",
        "sector": "Technology",
        "marketCap": 180_000_000,
        "price": 5.20,
        "volume": 2_100_000,
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
            "top_bearish": ["SOUN", "BBAI", "PATH"],
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
            "top_bearish": [],
        },
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
            "volume_ratio": 1.17,
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
            "volume_ratio": 0.79,
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
            "volume_ratio": 1.20,
        },
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
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slice1a: mark test as Slice 1A specific")
    config.addinivalue_line("markers", "slice1b: mark test as Slice 1B specific")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line(
        "markers", "external_apis: mark test as requiring external APIs"
    )
