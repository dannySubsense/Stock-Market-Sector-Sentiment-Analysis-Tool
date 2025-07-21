#!/usr/bin/env python3
"""
Unit Tests for UniverseBuilder Refactoring
Tests the enhanced sector case validation in _transform_fmp_to_database_format method
"""
import pytest
from unittest.mock import patch, MagicMock
from services.universe_builder import UniverseBuilder


class TestUniverseBuilderRefactoring:
    """Test the refactored UniverseBuilder with sector case validation"""

    def setup_method(self):
        """Setup test fixtures"""
        with patch("services.universe_builder.get_polygon_client"), patch(
            "services.universe_builder.get_fmp_client"
        ), patch("services.universe_builder.FMPSectorMapper"):
            self.universe_builder = UniverseBuilder()

    def test_transform_fmp_to_database_format_lowercase_sector(self):
        """Test transformation with already lowercase sector"""
        # Mock the get_weight_for_sector function
        with patch("services.universe_builder.get_weight_for_sector", return_value=1.2):
            fmp_stock = {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "exchange": "NASDAQ",
                "marketCap": 3000000000000,
                "volume": 50000000,
                "price": 150.0,
                "sector": "technology",  # Already lowercase
                "original_fmp_sector": "Technology",
            }

            result = self.universe_builder._transform_fmp_to_database_format(fmp_stock)

            # Verify sector remains lowercase
            assert result["sector"] == "technology"
            assert result["symbol"] == "AAPL"
            assert result["company_name"] == "Apple Inc."
            assert result["exchange"] == "NASDAQ"
            assert result["market_cap"] == 3000000000000
            assert result["avg_daily_volume"] == 50000000
            assert result["current_price"] == 150.0
            assert result["volatility_multiplier"] == 1.2

    def test_transform_fmp_to_database_format_uppercase_sector(self):
        """Test transformation with uppercase sector (should be converted)"""
        with patch(
            "services.universe_builder.get_weight_for_sector", return_value=1.1
        ) as mock_weight:
            fmp_stock = {
                "symbol": "MSFT",
                "companyName": "Microsoft Corporation",
                "exchange": "NASDAQ",
                "marketCap": 2500000000000,
                "volume": 40000000,
                "price": 300.0,
                "sector": "TECHNOLOGY",  # Uppercase - should be converted
                "original_fmp_sector": "Technology",
            }

            result = self.universe_builder._transform_fmp_to_database_format(fmp_stock)

            # Verify sector was converted to lowercase
            assert result["sector"] == "technology"
            # Verify get_weight_for_sector was called with lowercase sector
            mock_weight.assert_called_once_with("technology")

    def test_transform_fmp_to_database_format_mixed_case_sector(self):
        """Test transformation with mixed case sector"""
        with patch("services.universe_builder.get_weight_for_sector", return_value=0.9):
            fmp_stock = {
                "symbol": "JNJ",
                "companyName": "Johnson & Johnson",
                "exchange": "NYSE",
                "marketCap": 400000000000,
                "volume": 15000000,
                "price": 160.0,
                "sector": "HeAlThCaRe",  # Mixed case - should be converted
                "original_fmp_sector": "Healthcare",
            }

            result = self.universe_builder._transform_fmp_to_database_format(fmp_stock)

            # Verify sector was converted to lowercase
            assert result["sector"] == "healthcare"

    def test_transform_fmp_to_database_format_sector_with_spaces(self):
        """Test transformation with sector containing spaces and mixed case"""
        with patch("services.universe_builder.get_weight_for_sector", return_value=1.0):
            fmp_stock = {
                "symbol": "JPM",
                "companyName": "JPMorgan Chase & Co.",
                "exchange": "NYSE",
                "marketCap": 500000000000,
                "volume": 20000000,
                "price": 140.0,
                "sector": "Financial Services",  # Spaces and title case
                "original_fmp_sector": "Financial Services",
            }

            result = self.universe_builder._transform_fmp_to_database_format(fmp_stock)

            # Note: The FMPSectorMapper should have already converted this to financial_services
            # But our additional validation ensures it's lowercase
            assert result["sector"] == "financial services"  # Converted to lowercase

    def test_transform_fmp_to_database_format_unknown_sector(self):
        """Test transformation with unknown/default sector"""
        with patch("services.universe_builder.get_weight_for_sector", return_value=1.0):
            fmp_stock = {
                "symbol": "TEST",
                "companyName": "Test Company",
                "exchange": "NASDAQ",
                "marketCap": 100000000,
                "volume": 1000000,
                "price": 10.0,
                "sector": "unknown_sector",  # Default unknown sector
                "original_fmp_sector": "Unknown",
            }

            result = self.universe_builder._transform_fmp_to_database_format(fmp_stock)

            assert result["sector"] == "unknown_sector"

    def test_transform_fmp_to_database_format_missing_sector(self):
        """Test transformation when sector is missing"""
        with patch("services.universe_builder.get_weight_for_sector", return_value=1.0):
            fmp_stock = {
                "symbol": "TEST",
                "companyName": "Test Company",
                "exchange": "NASDAQ",
                "marketCap": 100000000,
                "volume": 1000000,
                "price": 10.0,
                # No sector field
                "original_fmp_sector": "",
            }

            result = self.universe_builder._transform_fmp_to_database_format(fmp_stock)

            # Should default to unknown_sector
            assert result["sector"] == "unknown_sector"

    def test_transform_fmp_to_database_format_sector_case_warning(self):
        """Test that non-lowercase sectors trigger warning log"""
        with patch(
            "services.universe_builder.get_weight_for_sector", return_value=1.0
        ), patch(
            "services.universe_builder.log_sector_normalization_warning"
        ) as mock_log_warning:

            fmp_stock = {
                "symbol": "TEST",
                "companyName": "Test Company",
                "exchange": "NASDAQ",
                "marketCap": 100000000,
                "volume": 1000000,
                "price": 10.0,
                "sector": "UPPERCASE_SECTOR",
                "original_fmp_sector": "Uppercase Sector",
            }

            result = self.universe_builder._transform_fmp_to_database_format(fmp_stock)

            # Verify warning was logged via pure function
            mock_log_warning.assert_called_once_with(
                "UPPERCASE_SECTOR", "uppercase_sector"
            )

            # Verify sector was converted
            assert result["sector"] == "uppercase_sector"

    def test_transform_fmp_to_database_format_preserves_other_fields(self):
        """Test that transformation preserves all other fields correctly"""
        with patch("services.universe_builder.get_weight_for_sector", return_value=1.5):
            fmp_stock = {
                "symbol": "NVDA",
                "companyName": "NVIDIA Corporation",
                "exchange": "NASDAQ",
                "marketCap": 1800000000000,
                "volume": 75000000,
                "price": 450.0,
                "sector": "Technology",
                "original_fmp_sector": "Technology",
                "extra_field": "should_be_preserved",  # Extra field from FMP
            }

            result = self.universe_builder._transform_fmp_to_database_format(fmp_stock)

            # Verify all expected fields are present and correct
            assert result["symbol"] == "NVDA"
            assert result["company_name"] == "NVIDIA Corporation"
            assert result["exchange"] == "NASDAQ"
            assert result["market_cap"] == 1800000000000
            assert result["avg_daily_volume"] == 75000000
            assert result["current_price"] == 450.0
            assert result["sector"] == "technology"  # Converted to lowercase
            assert result["original_fmp_sector"] == "Technology"
            assert result["volatility_multiplier"] == 1.5
            assert result["gap_frequency"] == "medium"

            # Extra field should not be included in our database format
            assert "extra_field" not in result

    def test_transform_fmp_to_database_format_edge_cases(self):
        """Test transformation with edge cases and invalid data"""
        with patch("services.universe_builder.get_weight_for_sector", return_value=1.0):
            test_cases = [
                # Empty sector
                {
                    "input": {
                        "symbol": "TEST1",
                        "companyName": "Test 1",
                        "exchange": "NYSE",
                        "marketCap": 100000000,
                        "volume": 1000000,
                        "price": 10.0,
                        "sector": "",
                        "original_fmp_sector": "",
                    },
                    "expected_sector": "unknown_sector",  # Pure function converts empty to unknown_sector
                },
                # None sector
                {
                    "input": {
                        "symbol": "TEST2",
                        "companyName": "Test 2",
                        "exchange": "NYSE",
                        "marketCap": 100000000,
                        "volume": 1000000,
                        "price": 10.0,
                        "sector": None,
                        "original_fmp_sector": "",
                    },
                    "expected_sector": "unknown_sector",  # Pure function converts None to unknown_sector
                },
                # Whitespace-only sector
                {
                    "input": {
                        "symbol": "TEST3",
                        "companyName": "Test 3",
                        "exchange": "NYSE",
                        "marketCap": 100000000,
                        "volume": 1000000,
                        "price": 10.0,
                        "sector": "   ",
                        "original_fmp_sector": "",
                    },
                    "expected_sector": "unknown_sector",  # Pure function converts whitespace to unknown_sector
                },
                # Missing sector key (should use default)
                {
                    "input": {
                        "symbol": "TEST4",
                        "companyName": "Test 4",
                        "exchange": "NYSE",
                        "marketCap": 100000000,
                        "volume": 1000000,
                        "price": 10.0,
                        # No sector key at all
                        "original_fmp_sector": "",
                    },
                    "expected_sector": "unknown_sector",  # Missing key uses default value
                },
            ]

            for case in test_cases:
                result = self.universe_builder._transform_fmp_to_database_format(
                    case["input"]
                )
                assert (
                    result["sector"] == case["expected_sector"]
                ), f"Failed for input: {case['input']['sector']}"


# Integration test with realistic sector mapper interaction
def test_universe_builder_integration_with_sector_mapper():
    """Integration test with realistic FMPSectorMapper interaction"""
    with patch("services.universe_builder.get_polygon_client"), patch(
        "services.universe_builder.get_fmp_client"
    ), patch("services.universe_builder.get_weight_for_sector", return_value=1.0):

        universe_builder = UniverseBuilder()

        # Simulate FMP data that has already been processed by FMPSectorMapper
        # (which should have normalized sector names)
        fmp_stocks = [
            {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "exchange": "NASDAQ",
                "marketCap": 3000000000000,
                "volume": 50000000,
                "price": 150.0,
                "sector": "technology",  # Already normalized by sector mapper
                "original_fmp_sector": "Technology",
            },
            {
                "symbol": "MSFT",
                "companyName": "Microsoft Corporation",
                "exchange": "NASDAQ",
                "marketCap": 2500000000000,
                "volume": 40000000,
                "price": 300.0,
                "sector": "TECHNOLOGY",  # Somehow still uppercase - should be caught
                "original_fmp_sector": "Technology",
            },
        ]

        results = []
        for fmp_stock in fmp_stocks:
            result = universe_builder._transform_fmp_to_database_format(fmp_stock)
            results.append(result)

        # Both should result in lowercase technology sector
        assert all(result["sector"] == "technology" for result in results)

        # All sectors should be lowercase
        assert all(result["sector"].islower() for result in results)

        # Should have no duplicate sectors due to case variations
        sectors = {result["sector"] for result in results}
        assert len(sectors) == 1  # Only 'technology'
        assert "technology" in sectors
