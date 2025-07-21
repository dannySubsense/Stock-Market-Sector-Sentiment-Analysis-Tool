#!/usr/bin/env python3
"""
TDD Tests for Pure Sector Normalization Functions
Written FIRST before implementation to follow proper TDD
"""
import pytest
from unittest.mock import patch
from services.sector_normalizer import (
    normalize_sector_name,
    log_sector_normalization_warning,
)


class TestNormalizeSectorName:
    """Test the pure sector normalization function"""

    def test_normalize_valid_lowercase_sector(self):
        """Test normalization of already lowercase sector"""
        result = normalize_sector_name("technology")
        assert result == "technology"

    def test_normalize_uppercase_sector(self):
        """Test normalization of uppercase sector"""
        result = normalize_sector_name("TECHNOLOGY")
        assert result == "technology"

    def test_normalize_mixed_case_sector(self):
        """Test normalization of mixed case sector"""
        result = normalize_sector_name("TeChnOlOgY")
        assert result == "technology"

    def test_normalize_sector_with_spaces(self):
        """Test normalization preserves spaces as-is"""
        result = normalize_sector_name("Financial Services")
        assert result == "financial services"

    def test_normalize_sector_with_whitespace(self):
        """Test normalization strips whitespace"""
        result = normalize_sector_name("  Technology  ")
        assert result == "technology"

    def test_normalize_empty_string(self):
        """Test normalization of empty string"""
        result = normalize_sector_name("")
        assert result == "unknown_sector"

    def test_normalize_whitespace_only(self):
        """Test normalization of whitespace-only string"""
        result = normalize_sector_name("   ")
        assert result == "unknown_sector"

    def test_normalize_none_input(self):
        """Test normalization of None input"""
        result = normalize_sector_name(None)
        assert result == "unknown_sector"

    def test_normalize_non_string_input(self):
        """Test normalization of non-string input"""
        result = normalize_sector_name(123)
        assert result == "unknown_sector"

        result = normalize_sector_name([])
        assert result == "unknown_sector"


class TestLogSectorNormalizationWarning:
    """Test the pure logging side effect function"""

    @patch("services.sector_normalizer.logger")
    def test_logs_warning_when_different(self, mock_logger):
        """Test that warning is logged when original differs from normalized"""
        log_sector_normalization_warning("TECHNOLOGY", "technology")
        mock_logger.warning.assert_called_once_with(
            'Sector normalized: "TECHNOLOGY" -> "technology"'
        )

    @patch("services.sector_normalizer.logger")
    def test_no_log_when_same(self, mock_logger):
        """Test that no warning is logged when original equals normalized"""
        log_sector_normalization_warning("technology", "technology")
        mock_logger.warning.assert_not_called()

    @patch("services.sector_normalizer.logger")
    def test_handles_empty_strings(self, mock_logger):
        """Test logging with empty strings"""
        log_sector_normalization_warning("", "unknown_sector")
        mock_logger.warning.assert_called_once_with(
            'Sector normalized: "" -> "unknown_sector"'
        )
