"""
FMP Sector Mapper Service
Provides ultra-simple 1:1 mapping from FMP sectors to internal sector names
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FMPSectorMapper:
    """
    Ultra-simple 1:1 FMP sector mapping - no complex classification needed
    Maps FMP's 11 professional sectors directly to internal names
    """

    def __init__(self):
        # Direct 1:1 mapping dictionary
        self.fmp_mapping = {
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

        # Theme slot placeholder configuration
        self.theme_slot_config = {
            "status": "placeholder",
            "slot_position": 12,
            "purpose": "hot_theme_tracking",
            "examples": [
                "Bitcoin Treasury", "AI Transformation", "Defense Spending"
            ],
            "ui_design": "different_styling_vs_regular_sectors",
        }

    def map_fmp_sector(self, fmp_sector: str) -> str:
        """
        Direct 1:1 mapping with 100% confidence

        Args:
            fmp_sector: The sector string from FMP data

        Returns:
            Internal sector name or 'unknown_sector' if not found
        """
        if not fmp_sector:
            return "unknown_sector"

        return self.fmp_mapping.get(fmp_sector, "unknown_sector")

    def get_all_sectors(self) -> List[str]:
        """
        Return all 11 mapped sectors + theme slot placeholder

        Returns:
            List of all sector names including theme_slot
        """
        sectors = list(self.fmp_mapping.values())
        sectors.append("theme_slot")  # Placeholder for slot 12
        return sectors

    def get_fmp_sectors(self) -> List[str]:
        """
        Return all original FMP sector names

        Returns:
            List of original FMP sector names
        """
        return list(self.fmp_mapping.keys())

    def get_theme_slot_info(self) -> Dict[str, Any]:
        """
        Return theme slot placeholder information

        Returns:
            Dictionary with theme slot configuration
        """
        return self.theme_slot_config.copy()

    def get_mapping_stats(self) -> Dict[str, Any]:
        """
        Return mapping statistics for validation

        Returns:
            Dictionary with mapping statistics
        """
        return {
            "total_fmp_sectors": len(self.fmp_mapping),
            "total_internal_sectors": len(self.fmp_mapping.values()),
            "total_slots": len(self.get_all_sectors()),  # 11 + 1 theme
            "has_theme_slot": True,
            "mapping_confidence": 1.0,  # 100% confidence for direct mapping
        }
