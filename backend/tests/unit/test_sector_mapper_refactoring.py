#!/usr/bin/env python3
"""
Unit Tests for FMPSectorMapper Refactoring
Tests the enhanced case standardization and normalization functionality
"""
import pytest
from services.sector_mapper import FMPSectorMapper


class TestFMPSectorMapperRefactoring:
    """Test the refactored FMPSectorMapper with case standardization"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mapper = FMPSectorMapper()

    def test_exact_match_standard_sectors(self):
        """Test exact matches for standard FMP sectors"""
        test_cases = [
            ("Technology", "technology"),
            ("Healthcare", "healthcare"),
            ("Energy", "energy"),
            ("Financial Services", "financial_services"),
            ("Basic Materials", "basic_materials"),
            ("Consumer Cyclical", "consumer_cyclical"),
            ("Consumer Defensive", "consumer_defensive"),
            ("Communication Services", "communication_services"),
            ("Industrials", "industrials"),
            ("Real Estate", "real_estate"),
            ("Utilities", "utilities"),
        ]

        for fmp_sector, expected_internal in test_cases:
            result = self.mapper.map_fmp_sector(fmp_sector)
            assert (
                result == expected_internal
            ), f"Expected {expected_internal}, got {result} for {fmp_sector}"

    def test_case_insensitive_mapping(self):
        """Test case-insensitive sector mapping"""
        test_cases = [
            ("TECHNOLOGY", "technology"),
            ("technology", "technology"),
            ("Technology", "technology"),
            ("TeChnOlOgY", "technology"),
            ("HEALTHCARE", "healthcare"),
            ("healthcare", "healthcare"),
            ("HeAlThCaRe", "healthcare"),
            ("FINANCIAL SERVICES", "financial_services"),
            ("financial services", "financial_services"),
            ("Financial Services", "financial_services"),
        ]

        for fmp_sector, expected_internal in test_cases:
            result = self.mapper.map_fmp_sector(fmp_sector)
            assert (
                result == expected_internal
            ), f"Case-insensitive mapping failed: {fmp_sector} -> {result}, expected {expected_internal}"

    def test_whitespace_normalization(self):
        """Test whitespace handling in sector names"""
        test_cases = [
            ("  Technology  ", "technology"),
            ("\tHealthcare\t", "healthcare"),
            ("\nEnergy\n", "energy"),
            ("  Financial Services  ", "financial_services"),
            ("   Basic Materials   ", "basic_materials"),
        ]

        for fmp_sector, expected_internal in test_cases:
            result = self.mapper.map_fmp_sector(fmp_sector)
            assert (
                result == expected_internal
            ), f"Whitespace normalization failed: '{fmp_sector}' -> {result}, expected {expected_internal}"

    def test_edge_cases(self):
        """Test edge cases and invalid inputs"""
        test_cases = [
            ("", "unknown_sector"),
            (None, "unknown_sector"),
            ("   ", "unknown_sector"),
            ("Invalid Sector", "unknown_sector"),
            ("Random Text", "unknown_sector"),
            ("Technology123", "unknown_sector"),
        ]

        for fmp_sector, expected_internal in test_cases:
            result = self.mapper.map_fmp_sector(fmp_sector)
            assert (
                result == expected_internal
            ), f"Edge case failed: {fmp_sector} -> {result}, expected {expected_internal}"

    def test_output_always_lowercase(self):
        """Test that output is always lowercase regardless of input case"""
        mixed_case_inputs = [
            "TECHNOLOGY",
            "Technology",
            "TeChnOlOgY",
            "healthcare",
            "HEALTHCARE",
            "HeAlThCaRe",
        ]

        for fmp_sector in mixed_case_inputs:
            result = self.mapper.map_fmp_sector(fmp_sector)
            assert result.islower(), f"Output not lowercase: {fmp_sector} -> {result}"
            assert (
                " " not in result or "_" in result
            ), f"Spaces not converted to underscores: {result}"

    def test_specific_technology_case_issue(self):
        """Test the specific Technology vs technology issue from the stress test"""
        # This tests the exact issue we found
        assert self.mapper.map_fmp_sector("Technology") == "technology"
        assert self.mapper.map_fmp_sector("technology") == "technology"
        assert self.mapper.map_fmp_sector("TECHNOLOGY") == "technology"

        # Both should map to the same internal sector
        result_capital = self.mapper.map_fmp_sector("Technology")
        result_lower = self.mapper.map_fmp_sector("technology")
        assert (
            result_capital == result_lower
        ), "Technology case variations should map to same sector"

    def test_all_fmp_sectors_covered(self):
        """Test that all expected FMP sectors are covered in mapping"""
        expected_fmp_sectors = [
            "Basic Materials",
            "Communication Services",
            "Consumer Cyclical",
            "Consumer Defensive",
            "Energy",
            "Financial Services",
            "Healthcare",
            "Industrials",
            "Real Estate",
            "Technology",
            "Utilities",
        ]

        for fmp_sector in expected_fmp_sectors:
            result = self.mapper.map_fmp_sector(fmp_sector)
            assert (
                result != "unknown_sector"
            ), f"Valid FMP sector {fmp_sector} mapped to unknown_sector"
            assert (
                result.islower()
            ), f"FMP sector {fmp_sector} result {result} is not lowercase"

    def test_sector_consistency_property(self):
        """Test that multiple calls with same input return same result"""
        test_inputs = ["Technology", "healthcare", "ENERGY", "  Financial Services  "]

        for fmp_sector in test_inputs:
            result1 = self.mapper.map_fmp_sector(fmp_sector)
            result2 = self.mapper.map_fmp_sector(fmp_sector)
            assert (
                result1 == result2
            ), f"Inconsistent results for {fmp_sector}: {result1} vs {result2}"

    def test_no_regression_existing_functionality(self):
        """Test that existing functionality still works correctly"""
        # Test methods that should still work
        all_sectors = self.mapper.get_all_sectors()
        assert len(all_sectors) >= 11, "Should have at least 11 sectors"
        assert "theme_slot" in all_sectors, "Should include theme_slot"

        fmp_sectors = self.mapper.get_fmp_sectors()
        assert len(fmp_sectors) == 11, "Should have exactly 11 FMP sectors"

        theme_info = self.mapper.get_theme_slot_info()
        assert "status" in theme_info, "Theme slot info should have status"

        stats = self.mapper.get_mapping_stats()
        assert stats["mapping_confidence"] == 1.0, "Should have 100% confidence"


# Integration test
def test_sector_mapper_integration_with_sample_data():
    """Integration test with realistic FMP data variations"""
    mapper = FMPSectorMapper()

    # Simulate real-world FMP data with case variations
    sample_fmp_data = [
        {"symbol": "AAPL", "sector": "Technology"},
        {"symbol": "MSFT", "sector": "technology"},
        {"symbol": "JNJ", "sector": "Healthcare"},
        {"symbol": "PFE", "sector": "HEALTHCARE"},
        {"symbol": "XOM", "sector": "Energy"},
        {"symbol": "CVX", "sector": "  Energy  "},
        {"symbol": "JPM", "sector": "Financial Services"},
        {"symbol": "BAC", "sector": "FINANCIAL SERVICES"},
    ]

    # Process through mapper
    mapped_sectors = set()
    for stock in sample_fmp_data:
        mapped_sector = mapper.map_fmp_sector(stock["sector"])
        mapped_sectors.add(mapped_sector)

        # Verify all results are lowercase
        assert (
            mapped_sector.islower()
        ), f"Mapped sector {mapped_sector} is not lowercase"

        # Verify no duplicates for same logical sector
        if "tech" in stock["sector"].lower():
            assert mapped_sector == "technology"
        elif "health" in stock["sector"].lower():
            assert mapped_sector == "healthcare"
        elif "energy" in stock["sector"].lower():
            assert mapped_sector == "energy"
        elif "financial" in stock["sector"].lower():
            assert mapped_sector == "financial_services"

    # Should have unique sectors (no case duplicates)
    assert (
        len(mapped_sectors) == 4
    ), f"Expected 4 unique sectors, got {len(mapped_sectors)}: {mapped_sectors}"
    assert "technology" in mapped_sectors
    assert "healthcare" in mapped_sectors
    assert "energy" in mapped_sectors
    assert "financial_services" in mapped_sectors
