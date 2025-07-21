"""
Unit Tests for 1D Stock Data Retrieval Service
Tests API comparison functionality and data validation
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.stock_data_retrieval_1d import (
    StockDataRetrieval1D,
    APITestResult,
    APIComparison,
)
from services.sector_performance_1d import StockData1D


class TestStockDataRetrieval1D:
    """Test class for 1D stock data retrieval service"""

    @pytest.fixture
    def retrieval_service(self):
        """Create stock data retrieval service with mocked clients"""
        with patch("services.stock_data_retrieval_1d.get_fmp_client"), patch(
            "services.stock_data_retrieval_1d.get_polygon_client"
        ):
            service = StockDataRetrieval1D()
            service.fmp_client = AsyncMock()
            service.polygon_client = AsyncMock()
            return service

    @pytest.fixture
    def sample_fmp_quote(self):
        """Sample FMP quote data"""
        return {
            "price": 25.50,
            "previousClose": 24.00,
            "volume": 1500000,
            "avgVolume": 1200000,
            "marketCap": 500000000,
            "open": 24.50,
            "high": 26.00,
            "low": 24.25,
        }

    @pytest.fixture
    def sample_polygon_quote(self):
        """Sample Polygon quote data"""
        return {
            "price": 25.45,
            "previousClose": 24.00,
            "volume": 1480000,
            "avgVolume": 1250000,
            "open": 24.55,
            "high": 25.95,
            "low": 24.30,
            "bid": 25.44,
            "ask": 25.46,
            "timestamp": 1640995200000,
        }

    @pytest.mark.asyncio
    async def test_validate_quote_data_valid_fmp(
        self, retrieval_service, sample_fmp_quote
    ):
        """Test quote data validation with valid FMP data"""
        score, issues = retrieval_service._validate_quote_data(sample_fmp_quote, "FMP")

        assert score >= 0.8  # Should be high quality
        assert (
            len(issues) <= 2
        )  # Minor issues only (missing bid/ask is expected for FMP)

        # Should not have missing required fields (price, previousClose, volume)
        required_missing = [
            issue
            for issue in issues
            if "Missing" in issue
            and any(field in issue for field in ["price", "previousClose", "volume"])
        ]
        assert (
            len(required_missing) == 0
        ), f"Should not have missing required fields: {required_missing}"

    @pytest.mark.asyncio
    async def test_validate_quote_data_valid_polygon(
        self, retrieval_service, sample_polygon_quote
    ):
        """Test quote data validation with valid Polygon data"""
        score, issues = retrieval_service._validate_quote_data(
            sample_polygon_quote, "Polygon"
        )

        assert score >= 0.8  # Should be high quality
        assert (
            len(issues) <= 2
        )  # Minor issues only (missing market cap is expected for Polygon)

    def test_validate_quote_data_missing_required_fields(self, retrieval_service):
        """Test validation with missing required fields"""
        incomplete_data = {
            "price": 25.50,
            # Missing previousClose and volume
        }

        score, issues = retrieval_service._validate_quote_data(incomplete_data, "FMP")

        assert score < 0.5  # Should be poor quality
        assert len(issues) >= 2  # Should have multiple issues
        assert any("Missing" in issue for issue in issues)

    def test_validate_quote_data_invalid_prices(self, retrieval_service):
        """Test validation with invalid price values"""
        invalid_data = {
            "price": -5.0,  # Negative price
            "previousClose": 0,  # Zero price
            "volume": 1000000,
        }

        score, issues = retrieval_service._validate_quote_data(invalid_data, "FMP")

        assert score < 0.5  # Should be poor quality
        assert any("Invalid" in issue for issue in issues)

    def test_validate_quote_data_extreme_price_change(self, retrieval_service):
        """Test validation with extreme price changes"""
        extreme_data = {
            "price": 100.0,
            "previousClose": 10.0,  # 900% increase
            "volume": 1000000,
        }

        score, issues = retrieval_service._validate_quote_data(extreme_data, "FMP")

        assert any("Extreme price change" in issue for issue in issues)

    @pytest.mark.asyncio
    async def test_fmp_api_success(self, retrieval_service, sample_fmp_quote):
        """Test successful FMP API call"""
        retrieval_service.fmp_client.get_quote.return_value = {
            "status": "success",
            "quote": sample_fmp_quote,
        }

        result = await retrieval_service._test_fmp_api("SOUN")

        assert result.success == True
        assert result.api_name == "FMP"
        assert result.symbol == "SOUN"
        assert result.data == sample_fmp_quote
        assert result.response_time_ms >= 0  # Allow 0 for mocked calls
        assert result.data_quality_score > 0

    @pytest.mark.asyncio
    async def test_fmp_api_failure(self, retrieval_service):
        """Test FMP API failure handling"""
        retrieval_service.fmp_client.get_quote.return_value = {
            "status": "error",
            "message": "API rate limit exceeded",
        }

        result = await retrieval_service._test_fmp_api("SOUN")

        assert result.success == False
        assert result.error_message == "API rate limit exceeded"
        assert result.data_quality_score == 0.0
        assert "API call failed" in result.validation_issues

    @pytest.mark.asyncio
    async def test_polygon_api_success(self, retrieval_service, sample_polygon_quote):
        """Test successful Polygon API call"""
        retrieval_service.polygon_client.get_quote_with_volume_avg.return_value = {
            "status": "success",
            "quote": sample_polygon_quote,
        }

        result = await retrieval_service._test_polygon_api("BBAI")

        assert result.success == True
        assert result.api_name == "Polygon"
        assert result.symbol == "BBAI"
        assert result.data == sample_polygon_quote
        assert result.response_time_ms >= 0  # Allow 0 for mocked calls
        assert result.data_quality_score > 0

    @pytest.mark.asyncio
    async def test_polygon_api_exception(self, retrieval_service):
        """Test Polygon API exception handling"""
        retrieval_service.polygon_client.get_quote_with_volume_avg.side_effect = (
            Exception("Network timeout")
        )

        result = await retrieval_service._test_polygon_api("BBAI")

        assert result.success == False
        assert "Network timeout" in result.error_message
        assert result.data_quality_score == 0.0

    def test_calculate_data_consistency_high(self, retrieval_service):
        """Test data consistency calculation with similar data"""
        fmp_data = {"price": 25.50, "volume": 1500000}
        polygon_data = {"price": 25.52, "volume": 1480000}  # Very close values

        consistency = retrieval_service._calculate_data_consistency(
            fmp_data, polygon_data
        )

        assert consistency >= 0.8  # Should be high consistency

    def test_calculate_data_consistency_low(self, retrieval_service):
        """Test data consistency calculation with different data"""
        fmp_data = {"price": 25.50, "volume": 1500000}
        polygon_data = {"price": 30.00, "volume": 500000}  # Very different values

        consistency = retrieval_service._calculate_data_consistency(
            fmp_data, polygon_data
        )

        assert consistency < 0.5  # Should be low consistency

    def test_determine_api_recommendation_fmp_wins(self, retrieval_service):
        """Test API recommendation when FMP is better"""
        fmp_result = APITestResult(
            api_name="FMP",
            symbol="TEST",
            success=True,
            response_time_ms=100,
            data={"price": 25.0},
            error_message=None,
            data_quality_score=0.9,
            validation_issues=[],
        )

        polygon_result = APITestResult(
            api_name="Polygon",
            symbol="TEST",
            success=True,
            response_time_ms=200,
            data={"price": 25.0},
            error_message=None,
            data_quality_score=0.7,
            validation_issues=["Missing field"],
        )

        api, reason = retrieval_service._determine_api_recommendation(
            fmp_result, polygon_result, 0.9
        )

        assert api == "FMP"
        assert "higher data quality" in reason

    def test_determine_api_recommendation_polygon_wins(self, retrieval_service):
        """Test API recommendation when Polygon is better"""
        fmp_result = APITestResult(
            api_name="FMP",
            symbol="TEST",
            success=True,
            response_time_ms=300,
            data={"price": 25.0},
            error_message=None,
            data_quality_score=0.6,
            validation_issues=["Missing field", "Invalid data"],
        )

        polygon_result = APITestResult(
            api_name="Polygon",
            symbol="TEST",
            success=True,
            response_time_ms=150,
            data={"price": 25.0},
            error_message=None,
            data_quality_score=0.8,
            validation_issues=[],
        )

        api, reason = retrieval_service._determine_api_recommendation(
            fmp_result, polygon_result, 0.9
        )

        assert api == "Polygon"
        assert "higher data quality" in reason or "faster response" in reason

    def test_determine_api_recommendation_only_fmp_succeeds(self, retrieval_service):
        """Test recommendation when only FMP succeeds"""
        fmp_result = APITestResult(
            api_name="FMP",
            symbol="TEST",
            success=True,
            response_time_ms=100,
            data={"price": 25.0},
            error_message=None,
            data_quality_score=0.8,
            validation_issues=[],
        )

        polygon_result = APITestResult(
            api_name="Polygon",
            symbol="TEST",
            success=False,
            response_time_ms=0,
            data=None,
            error_message="API error",
            data_quality_score=0.0,
            validation_issues=["API call failed"],
        )

        api, reason = retrieval_service._determine_api_recommendation(
            fmp_result, polygon_result, 0.0
        )

        assert api == "FMP"
        assert "Only FMP succeeded" in reason

    def test_determine_api_recommendation_both_fail(self, retrieval_service):
        """Test recommendation when both APIs fail"""
        fmp_result = APITestResult(
            api_name="FMP",
            symbol="TEST",
            success=False,
            response_time_ms=0,
            data=None,
            error_message="FMP error",
            data_quality_score=0.0,
            validation_issues=["API call failed"],
        )

        polygon_result = APITestResult(
            api_name="Polygon",
            symbol="TEST",
            success=False,
            response_time_ms=0,
            data=None,
            error_message="Polygon error",
            data_quality_score=0.0,
            validation_issues=["API call failed"],
        )

        api, reason = retrieval_service._determine_api_recommendation(
            fmp_result, polygon_result, 0.0
        )

        assert api == "Neither"
        assert "Both APIs failed" in reason

    def test_convert_to_stock_data_1d(self, retrieval_service, sample_fmp_quote):
        """Test conversion from quote data to StockData1D"""
        stock_data = retrieval_service._convert_to_stock_data_1d(
            "SOUN", sample_fmp_quote
        )

        assert isinstance(stock_data, StockData1D)
        assert stock_data.symbol == "SOUN"
        assert stock_data.current_price == 25.50
        assert stock_data.previous_close == 24.00
        assert stock_data.current_volume == 1500000
        assert stock_data.avg_20_day_volume == 1200000

    def test_convert_to_stock_data_1d_missing_avg_volume(self, retrieval_service):
        """Test conversion when average volume is missing"""
        quote_data = {
            "price": 25.50,
            "previousClose": 24.00,
            "volume": 1500000,
            # Missing avgVolume
        }

        stock_data = retrieval_service._convert_to_stock_data_1d("TEST", quote_data)

        assert (
            stock_data.avg_20_day_volume == 1500000
        )  # Should use current volume as fallback

    @pytest.mark.asyncio
    async def test_get_1d_stock_data_auto_mode_fmp_success(
        self, retrieval_service, sample_fmp_quote
    ):
        """Test get_1d_stock_data in auto mode with FMP success"""
        # Mock FMP to succeed with high quality
        retrieval_service.fmp_client.get_quote.return_value = {
            "status": "success",
            "quote": sample_fmp_quote,
        }

        # Should not call Polygon since FMP succeeds
        result = await retrieval_service.get_1d_stock_data("SOUN", "auto")

        assert isinstance(result, StockData1D)
        assert result.symbol == "SOUN"
        assert result.current_price == 25.50

        # Verify FMP was called but Polygon was not
        retrieval_service.fmp_client.get_quote.assert_called_once_with("SOUN")
        retrieval_service.polygon_client.get_quote_with_volume_avg.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_1d_stock_data_auto_mode_fallback_to_polygon(
        self, retrieval_service, sample_polygon_quote
    ):
        """Test get_1d_stock_data auto mode falling back to Polygon"""
        # Mock FMP to fail
        retrieval_service.fmp_client.get_quote.return_value = {
            "status": "error",
            "message": "API error",
        }

        # Mock Polygon to succeed
        retrieval_service.polygon_client.get_quote_with_volume_avg.return_value = {
            "status": "success",
            "quote": sample_polygon_quote,
        }

        result = await retrieval_service.get_1d_stock_data("BBAI", "auto")

        assert isinstance(result, StockData1D)
        assert result.symbol == "BBAI"
        assert result.current_price == 25.45

        # Verify both APIs were called
        retrieval_service.fmp_client.get_quote.assert_called_once_with("BBAI")
        retrieval_service.polygon_client.get_quote_with_volume_avg.assert_called_once_with(
            "BBAI"
        )

    @pytest.mark.asyncio
    async def test_get_1d_stock_data_fmp_mode(
        self, retrieval_service, sample_fmp_quote
    ):
        """Test get_1d_stock_data in FMP-only mode"""
        retrieval_service.fmp_client.get_quote.return_value = {
            "status": "success",
            "quote": sample_fmp_quote,
        }

        result = await retrieval_service.get_1d_stock_data("PATH", "fmp")

        assert isinstance(result, StockData1D)
        assert result.symbol == "PATH"

        # Verify only FMP was called
        retrieval_service.fmp_client.get_quote.assert_called_once_with("PATH")
        retrieval_service.polygon_client.get_quote_with_volume_avg.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_1d_stock_data_polygon_mode(
        self, retrieval_service, sample_polygon_quote
    ):
        """Test get_1d_stock_data in Polygon-only mode"""
        retrieval_service.polygon_client.get_quote_with_volume_avg.return_value = {
            "status": "success",
            "quote": sample_polygon_quote,
        }

        result = await retrieval_service.get_1d_stock_data("OCUL", "polygon")

        assert isinstance(result, StockData1D)
        assert result.symbol == "OCUL"

        # Verify only Polygon was called
        retrieval_service.polygon_client.get_quote_with_volume_avg.assert_called_once_with(
            "OCUL"
        )
        retrieval_service.fmp_client.get_quote.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_1d_stock_data_both_apis_fail(self, retrieval_service):
        """Test get_1d_stock_data when both APIs fail"""
        # Mock both APIs to fail
        retrieval_service.fmp_client.get_quote.return_value = {
            "status": "error",
            "message": "FMP error",
        }

        retrieval_service.polygon_client.get_quote_with_volume_avg.return_value = {
            "status": "error",
            "message": "Polygon error",
        }

        result = await retrieval_service.get_1d_stock_data("SMCI", "auto")

        assert result is None

    def test_extract_data_preview(self, retrieval_service, sample_fmp_quote):
        """Test data preview extraction"""
        preview = retrieval_service._extract_data_preview(sample_fmp_quote)

        expected_fields = ["price", "previousClose", "volume", "avgVolume", "marketCap"]
        for field in expected_fields:
            if field in sample_fmp_quote:
                assert field in preview
                assert preview[field] == sample_fmp_quote[field]

    def test_extract_data_preview_empty_data(self, retrieval_service):
        """Test data preview extraction with empty data"""
        preview = retrieval_service._extract_data_preview({})
        assert preview == {}

        preview = retrieval_service._extract_data_preview(None)
        assert preview == {}

    def test_build_recommendation_reasoning(self, retrieval_service):
        """Test recommendation reasoning text generation"""
        reasoning = retrieval_service._build_recommendation_reasoning(
            fmp_wins=3,
            polygon_wins=1,
            ties=1,
            failures=0,
            fmp_quality=0.85,
            polygon_quality=0.72,
            consistency=0.9,
        )

        assert "FMP performed better" in reasoning
        assert "3/5 tests" in reasoning
        assert "0.85" in reasoning  # FMP quality
        assert "0.72" in reasoning  # Polygon quality
        assert "0.9" in reasoning  # Consistency
