"""
Unit tests for FMPSectorMapper class
Tests the 1:1 mapping from FMP sectors to internal sector names
"""

import sys
from pathlib import Path

from services.sector_mapper import FMPSectorMapper

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


class TestFMPSectorMapper:
    """Test suite for FMPSectorMapper class"""

    def setup_method(self):
        """Setup test instance"""
        self.mapper = FMPSectorMapper()

    def test_map_valid_fmp_sectors(self):
        """Test mapping of all valid FMP sectors"""
        # Test all 11 FMP sectors map correctly
        valid_mappings = {
            "Basic Materials": "basic_materials",
            "Communication Services": "communication_services",
            "Consumer Cyclical": "consumer_cyclical",
            "Consumer Defensive": "consumer_defensive",
            "Energy": "energy",
            "Financial Services": "financial_services",
            "Healthcare": "healthcare",
            "Industrials": "industrials",
            "Real Estate": "real_estate",
            "Technology": "technology",
            "Utilities": "utilities",
        }

        for fmp_sector, expected_internal in valid_mappings.items():
            result = self.mapper.map_fmp_sector(fmp_sector)
            assert (
                result == expected_internal
            ), f"Expected {expected_internal} for {fmp_sector}, got {result}"

    def test_map_unknown_sector(self):
        """Test handling of unknown/invalid FMP sectors"""
        unknown_sectors = ["Unknown Sector", "", "Invalid", None]

        for unknown in unknown_sectors:
            result = self.mapper.map_fmp_sector(unknown)
            assert (
                result == "unknown_sector"
            ), f"Expected 'unknown_sector' for {unknown}, got {result}"

    def test_get_all_sectors_includes_eleven_fmp_sectors(self):
        """Test that get_all_sectors returns all 11 mapped sectors"""
        sectors = self.mapper.get_all_sectors()

        expected_sectors = [
            "basic_materials",
            "communication_services",
            "consumer_cyclical",
            "consumer_defensive",
            "energy",
            "financial_services",
            "healthcare",
            "industrials",
            "real_estate",
            "technology",
            "utilities",
        ]

        # Check all expected sectors are present
        for expected in expected_sectors:
            assert expected in sectors, f"Missing sector: {expected}"

        # Check we have at least 11 sectors
        assert len(sectors) >= 11, f"Expected at least 11 sectors, got {len(sectors)}"

    def test_get_all_sectors_includes_theme_slot(self):
        """Test that get_all_sectors includes theme slot placeholder"""
        sectors = self.mapper.get_all_sectors()

        assert "theme_slot" in sectors, "Missing theme_slot placeholder"
        assert (
            len(sectors) == 12
        ), f"Expected exactly 12 slots (11 + theme), got {len(sectors)}"

    def test_mapping_is_case_insensitive(self):
        """Test that sector mapping is case insensitive (post-refactoring)"""
        # FMP sectors should work regardless of case
        assert (
            self.mapper.map_fmp_sector("technology") == "technology"
        )  # lowercase should work
        assert (
            self.mapper.map_fmp_sector("Technology") == "technology"
        )  # title case should work
        assert (
            self.mapper.map_fmp_sector("TECHNOLOGY") == "technology"
        )  # uppercase should work

    def test_get_theme_slot_info(self):
        """Test theme slot placeholder information"""
        theme_info = self.mapper.get_theme_slot_info()

        assert isinstance(theme_info, dict)
        assert theme_info["status"] == "placeholder"
        assert "slot_position" in theme_info
        assert theme_info["slot_position"] == 12
        assert "purpose" in theme_info
        assert "examples" in theme_info
