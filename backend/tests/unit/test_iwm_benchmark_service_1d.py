"""
Unit Tests for IWM Benchmark Service - Step 4 Implementation
Tests all core functionality: data retrieval, caching, calculations, error handling
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from dataclasses import dataclass

from services.iwm_benchmark_service_1d import (
    IWMBenchmarkService1D,
    IWMBenchmarkData1D,
    get_iwm_service,
)
from services.sector_performance_1d import StockData1D


class TestIWMBenchmarkService1D:
    """Unit tests for IWM Benchmark Service"""

    @pytest.fixture
    def service(self):
        """Create IWM service instance for testing"""
        return IWMBenchmarkService1D()

    @pytest.fixture
    def sample_iwm_stock_data(self):
        """Sample IWM stock data for testing"""
        return StockData1D(
            symbol="IWM",
            current_price=200.0,
            previous_close=198.0,
            current_volume=5000000,
            avg_20_day_volume=4000000,
            sector="",  # ETF doesn't have sector
        )

    @pytest.fixture
    def sample_cached_iwm_data(self):
        """Sample cached IWM data"""
        return {
            "performance_1d": 1.010,
            "current_price": 200.0,
            "previous_close": 198.0,
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "FMP",
            "confidence": 0.95,
            "cached_at": datetime.utcnow().isoformat(),
            "cache_ttl": 300,
        }

    @pytest.fixture
    def stale_cached_iwm_data(self):
        """Sample stale cached IWM data"""
        stale_time = datetime.utcnow() - timedelta(hours=2)
        return {
            "performance_1d": 0.500,
            "current_price": 195.0,
            "previous_close": 194.0,
            "timestamp": stale_time.isoformat(),
            "data_source": "CACHE",
            "confidence": 0.8,
            "cached_at": stale_time.isoformat(),
            "cache_ttl": 300,
        }

    def test_iwm_service_initialization(self, service):
        """Test IWM service initializes correctly"""
        assert service.IWM_SYMBOL == "IWM"
        assert service.CACHE_TTL_MARKET_HOURS == 300
        assert service.CACHE_TTL_AFTER_HOURS == 3600
        assert service.MIN_PRICE == 50.0
        assert service.MAX_PRICE == 500.0
        assert service.MAX_DAILY_CHANGE == 20.0
        assert service.data_retrieval is not None
        assert service.cache_service is not None
        # Verify threshold constants are present
        assert service.STRONG_OUTPERFORM_THRESHOLD == 2.0
        assert service.OUTPERFORM_THRESHOLD == 0.5
        assert service.NEUTRAL_THRESHOLD == -0.5
        assert service.UNDERPERFORM_THRESHOLD == -2.0

    def test_get_iwm_service_singleton(self):
        """Test get_iwm_service returns singleton instance"""
        service1 = get_iwm_service()
        service2 = get_iwm_service()
        assert service1 is service2
        assert isinstance(service1, IWMBenchmarkService1D)

    def test_validate_iwm_data_valid(self, service, sample_iwm_stock_data):
        """Test IWM data validation with valid data"""
        assert service._validate_iwm_data(sample_iwm_stock_data) is True

    def test_validate_iwm_data_invalid_price_range(
        self, service, sample_iwm_stock_data
    ):
        """Test IWM data validation with invalid price ranges"""
        # Test current price too low
        sample_iwm_stock_data.current_price = 10.0
        assert service._validate_iwm_data(sample_iwm_stock_data) is False

        # Test current price too high
        sample_iwm_stock_data.current_price = 1000.0
        assert service._validate_iwm_data(sample_iwm_stock_data) is False

        # Test previous close too low
        sample_iwm_stock_data.current_price = 200.0
        sample_iwm_stock_data.previous_close = 10.0
        assert service._validate_iwm_data(sample_iwm_stock_data) is False

    def test_validate_iwm_data_invalid_change(self, service, sample_iwm_stock_data):
        """Test IWM data validation with excessive daily change"""
        # Test excessive positive change (>20%)
        sample_iwm_stock_data.current_price = 250.0
        sample_iwm_stock_data.previous_close = 200.0
        assert service._validate_iwm_data(sample_iwm_stock_data) is False

        # Test excessive negative change (>20%)
        sample_iwm_stock_data.current_price = 150.0
        sample_iwm_stock_data.previous_close = 200.0
        assert service._validate_iwm_data(sample_iwm_stock_data) is False

    def test_validate_iwm_data_invalid_volume(self, service, sample_iwm_stock_data):
        """Test IWM data validation with invalid volume"""
        sample_iwm_stock_data.current_volume = -1000
        assert service._validate_iwm_data(sample_iwm_stock_data) is False

    def test_validate_iwm_data_none(self, service):
        """Test IWM data validation with None data"""
        assert service._validate_iwm_data(None) is False

    def test_calculate_data_confidence_high_volume(
        self, service, sample_iwm_stock_data
    ):
        """Test confidence calculation with high quality data"""
        confidence = service._calculate_data_confidence(sample_iwm_stock_data)

        # Should be high confidence with normal volume and small change
        assert 0.9 <= confidence <= 1.0
        assert isinstance(confidence, float)

    def test_calculate_data_confidence_low_volume(self, service, sample_iwm_stock_data):
        """Test confidence calculation with low volume"""
        sample_iwm_stock_data.current_volume = 500000  # Low volume
        confidence = service._calculate_data_confidence(sample_iwm_stock_data)

        # Should be reduced confidence due to low volume
        assert 0.7 <= confidence <= 0.9

    def test_calculate_data_confidence_large_change(
        self, service, sample_iwm_stock_data
    ):
        """Test confidence calculation with large price change"""
        sample_iwm_stock_data.current_price = 220.0  # +11% change
        confidence = service._calculate_data_confidence(sample_iwm_stock_data)

        # Should be reduced confidence due to large change
        assert 0.7 <= confidence <= 0.9

    def test_calculate_data_confidence_no_volume_history(self, service):
        """Test confidence calculation with no volume history"""
        iwm_data_no_history = StockData1D(
            symbol="IWM",
            current_price=200.0,
            previous_close=198.0,
            current_volume=5000000,
            avg_20_day_volume=0,  # No history
            sector="",
        )

        confidence = service._calculate_data_confidence(iwm_data_no_history)
        assert 0.8 <= confidence <= 1.0  # Reduced due to no history

    def test_calculate_sector_alpha(self, service):
        """Test sector alpha calculation"""
        # Test positive alpha (outperformance)
        alpha = service.calculate_sector_alpha(5.0, 2.0)
        assert alpha == 3.0

        # Test negative alpha (underperformance)
        alpha = service.calculate_sector_alpha(1.0, 3.0)
        assert alpha == -2.0

        # Test neutral alpha
        alpha = service.calculate_sector_alpha(2.5, 2.5)
        assert alpha == 0.0

        # Test rounding
        alpha = service.calculate_sector_alpha(5.1234, 2.6789)
        assert alpha == 2.445

    def test_classify_relative_strength_delegation(self, service):
        """Test that relative strength classification delegates to existing logic"""
        # Test all classification ranges
        assert service.classify_relative_strength(3.0) == "STRONG_OUTPERFORM"
        assert service.classify_relative_strength(1.0) == "OUTPERFORM"
        assert service.classify_relative_strength(0.0) == "NEUTRAL"
        assert service.classify_relative_strength(-1.0) == "UNDERPERFORM"
        assert service.classify_relative_strength(-3.0) == "STRONG_UNDERPERFORM"

    def test_is_cache_fresh_market_hours(self, service, sample_cached_iwm_data):
        """Test cache freshness during market hours"""
        # Mock market hours (hour 10 = 10 AM)
        with patch("services.iwm_benchmark_service_1d.datetime") as mock_datetime:
            mock_now = datetime.utcnow().replace(hour=10)  # Market hours
            mock_datetime.utcnow.return_value = mock_now
            mock_datetime.fromisoformat.return_value = mock_now - timedelta(
                minutes=2
            )  # 2 minutes old

            # Should be fresh (2 minutes < 5 minute TTL)
            assert service._is_cache_fresh(sample_cached_iwm_data) is True

    def test_is_cache_fresh_after_hours(self, service, sample_cached_iwm_data):
        """Test cache freshness after market hours"""
        with patch("services.iwm_benchmark_service_1d.datetime") as mock_datetime:
            mock_now = datetime.utcnow().replace(hour=20)  # After hours
            mock_datetime.utcnow.return_value = mock_now
            mock_datetime.fromisoformat.return_value = mock_now - timedelta(
                minutes=30
            )  # 30 minutes old

            # Should be fresh (30 minutes < 60 minute after-hours TTL)
            assert service._is_cache_fresh(sample_cached_iwm_data) is True

    def test_is_cache_stale(self, service, stale_cached_iwm_data):
        """Test cache staleness detection"""
        # Should be stale (2 hours old > any TTL)
        assert service._is_cache_fresh(stale_cached_iwm_data) is False

    def test_parse_cached_iwm_data(self, service, sample_cached_iwm_data):
        """Test parsing cached data into IWMBenchmarkData1D object"""
        parsed = service._parse_cached_iwm_data(sample_cached_iwm_data)

        assert isinstance(parsed, IWMBenchmarkData1D)
        assert parsed.performance_1d == 1.010
        assert parsed.current_price == 200.0
        assert parsed.previous_close == 198.0
        assert parsed.data_source == "FMP"
        assert parsed.cache_status == "cached"
        assert parsed.confidence == 0.95
        assert isinstance(parsed.timestamp, datetime)

    def test_get_neutral_benchmark(self, service):
        """Test neutral benchmark fallback"""
        neutral = service._get_neutral_benchmark()

        assert isinstance(neutral, IWMBenchmarkData1D)
        assert neutral.performance_1d == 0.0
        assert neutral.current_price == 200.0
        assert neutral.previous_close == 200.0
        assert neutral.data_source == "FALLBACK"
        assert neutral.cache_status == "none"
        assert neutral.confidence == 0.1

    @pytest.mark.asyncio
    async def test_get_cached_iwm_benchmark_1d_cache_hit(
        self, service, sample_cached_iwm_data
    ):
        """Test get_cached_iwm_benchmark_1d with cache hit"""
        # Mock cache service to return fresh data
        service.cache_service.get_cached_iwm_benchmark_1d = AsyncMock(
            return_value=sample_cached_iwm_data
        )

        with patch.object(service, "_is_cache_fresh", return_value=True):
            result = await service.get_cached_iwm_benchmark_1d()

            assert isinstance(result, IWMBenchmarkData1D)
            assert result.performance_1d == 1.010
            assert result.cache_status == "cached"
            service.cache_service.get_cached_iwm_benchmark_1d.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_iwm_benchmark_1d_cache_miss(
        self, service, sample_iwm_stock_data
    ):
        """Test get_cached_iwm_benchmark_1d with cache miss"""
        # Mock cache miss
        service.cache_service.get_cached_iwm_benchmark_1d = AsyncMock(return_value=None)
        service.cache_service.cache_iwm_benchmark_1d = AsyncMock(return_value=True)

        # Mock refresh_iwm_data to return fresh data
        fresh_data = IWMBenchmarkData1D(
            performance_1d=1.010,
            current_price=200.0,
            previous_close=198.0,
            timestamp=datetime.utcnow(),
            data_source="API_AUTO",
            cache_status="fresh",
            confidence=0.95,
        )

        with patch.object(service, "refresh_iwm_data", return_value=fresh_data):
            result = await service.get_cached_iwm_benchmark_1d()

            assert isinstance(result, IWMBenchmarkData1D)
            assert result.performance_1d == 1.010
            assert result.cache_status == "fresh"
            service.cache_service.get_cached_iwm_benchmark_1d.assert_called_once()
            service.cache_service.cache_iwm_benchmark_1d.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_iwm_benchmark_1d_stale_fallback(
        self, service, stale_cached_iwm_data
    ):
        """Test get_cached_iwm_benchmark_1d with stale cache fallback"""
        # Mock stale cache data
        service.cache_service.get_cached_iwm_benchmark_1d = AsyncMock(
            return_value=stale_cached_iwm_data
        )

        # Mock refresh to fail
        with patch.object(
            service, "refresh_iwm_data", side_effect=Exception("API failed")
        ):
            with patch.object(service, "_is_cache_fresh", return_value=False):
                result = await service.get_cached_iwm_benchmark_1d()

                assert isinstance(result, IWMBenchmarkData1D)
                assert result.cache_status == "stale"
                assert result.confidence < 0.8  # Reduced confidence for stale data

    @pytest.mark.asyncio
    async def test_get_cached_iwm_benchmark_1d_total_failure(self, service):
        """Test get_cached_iwm_benchmark_1d with total failure"""
        # Mock total failure - no cache, refresh fails
        service.cache_service.get_cached_iwm_benchmark_1d = AsyncMock(return_value=None)

        with patch.object(
            service, "refresh_iwm_data", side_effect=Exception("All APIs failed")
        ):
            result = await service.get_cached_iwm_benchmark_1d()

            assert isinstance(result, IWMBenchmarkData1D)
            assert result.data_source == "FALLBACK"
            assert result.performance_1d == 0.0
            assert result.confidence == 0.1

    @pytest.mark.asyncio
    async def test_refresh_iwm_data_auto_success(self, service, sample_iwm_stock_data):
        """Test refresh_iwm_data with auto mode success"""
        # Mock successful auto retrieval
        service.data_retrieval.get_1d_stock_data = AsyncMock(
            return_value=sample_iwm_stock_data
        )

        result = await service.refresh_iwm_data()

        assert isinstance(result, IWMBenchmarkData1D)
        assert result.performance_1d == 1.010  # (200-198)/198*100
        assert result.current_price == 200.0
        assert result.previous_close == 198.0
        assert (
            result.data_source == "POLYGON"
        )  # Updated to match Polygon-first refactoring
        assert result.cache_status == "fresh"
        assert 0.0 <= result.confidence <= 1.0

        # Verify get_1d_stock_data was called with correct parameters
        service.data_retrieval.get_1d_stock_data.assert_called_with("IWM", "polygon")

    @pytest.mark.asyncio
    async def test_refresh_iwm_data_fmp_fallback(self, service, sample_iwm_stock_data):
        """Test refresh_iwm_data with FMP fallback"""
        # Mock auto failure, FMP success
        service.data_retrieval.get_1d_stock_data = AsyncMock(
            side_effect=[None, sample_iwm_stock_data]
        )

        result = await service.refresh_iwm_data()

        assert isinstance(result, IWMBenchmarkData1D)
        assert result.data_source == "FMP"
        assert result.performance_1d == 1.010

        assert service.data_retrieval.get_1d_stock_data.call_count == 2
        service.data_retrieval.get_1d_stock_data.assert_any_call("IWM", "polygon")
        service.data_retrieval.get_1d_stock_data.assert_any_call("IWM", "fmp")

    @pytest.mark.asyncio
    async def test_refresh_iwm_data_polygon_fallback(
        self, service, sample_iwm_stock_data
    ):
        """Test refresh_iwm_data with Polygon primary success"""
        # Mock Polygon success (primary API)
        service.data_retrieval.get_1d_stock_data = AsyncMock(
            return_value=sample_iwm_stock_data
        )

        result = await service.refresh_iwm_data()

        assert isinstance(result, IWMBenchmarkData1D)
        assert result.data_source == "POLYGON"
        assert result.performance_1d == 1.010

        assert service.data_retrieval.get_1d_stock_data.call_count == 1
        service.data_retrieval.get_1d_stock_data.assert_any_call("IWM", "polygon")

    @pytest.mark.asyncio
    async def test_refresh_iwm_data_total_failure(self, service):
        """Test refresh_iwm_data with all APIs failing"""
        # Mock all APIs failing
        service.data_retrieval.get_1d_stock_data = AsyncMock(return_value=None)

        with pytest.raises(Exception, match="All IWM data sources failed"):
            await service.refresh_iwm_data()

        assert service.data_retrieval.get_1d_stock_data.call_count == 2

    @pytest.mark.asyncio
    async def test_refresh_iwm_data_invalid_data(self, service):
        """Test refresh_iwm_data with invalid data from API"""
        # Mock API returning invalid data
        invalid_data = StockData1D(
            symbol="IWM",
            current_price=10.0,  # Invalid - too low
            previous_close=198.0,
            current_volume=5000000,
            avg_20_day_volume=4000000,
            sector="",
        )

        service.data_retrieval.get_1d_stock_data = AsyncMock(return_value=invalid_data)

        with pytest.raises(Exception, match="All IWM data sources failed"):
            await service.refresh_iwm_data()

    @pytest.mark.asyncio
    async def test_get_iwm_health_check_healthy(self, service):
        """Test IWM health check when all services are healthy"""
        # Mock healthy cache and API
        service.cache_service.health_check = AsyncMock(
            return_value={"status": "healthy"}
        )
        service.data_retrieval.get_1d_stock_data = AsyncMock(
            return_value=StockData1D(
                symbol="IWM",
                current_price=200.0,
                previous_close=198.0,
                current_volume=5000000,
                avg_20_day_volume=4000000,
                sector="",
            )
        )

        result = await service.get_iwm_health_check()

        assert result["status"] == "healthy"
        assert result["cache_status"] == "healthy"
        assert result["api_status"] == "healthy"
        assert result["api_response_time_ms"] >= 0
        assert result["total_response_time_ms"] >= 0
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_iwm_health_check_degraded(self, service):
        """Test IWM health check when services are degraded"""
        # Mock unhealthy cache
        service.cache_service.health_check = AsyncMock(
            return_value={"status": "unhealthy"}
        )
        service.data_retrieval.get_1d_stock_data = AsyncMock(return_value=None)

        result = await service.get_iwm_health_check()

        assert result["status"] == "degraded"
        assert result["cache_status"] == "unhealthy"
        assert result["api_status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_cache_iwm_data(self, service):
        """Test caching IWM data"""
        iwm_data = IWMBenchmarkData1D(
            performance_1d=1.010,
            current_price=200.0,
            previous_close=198.0,
            timestamp=datetime.utcnow(),
            data_source="FMP",
            cache_status="fresh",
            confidence=0.95,
        )

        service.cache_service.cache_iwm_benchmark_1d = AsyncMock(return_value=True)

        result = await service._cache_iwm_data(iwm_data)

        assert result is True
        service.cache_service.cache_iwm_benchmark_1d.assert_called_once()

        # Verify cache data structure
        call_args = service.cache_service.cache_iwm_benchmark_1d.call_args[0][0]
        assert call_args["performance_1d"] == 1.010
        assert call_args["current_price"] == 200.0
        assert call_args["data_source"] == "FMP"
        assert call_args["confidence"] == 0.95
        assert "cached_at" in call_args
