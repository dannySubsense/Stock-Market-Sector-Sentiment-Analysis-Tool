"""
FMP Sector Mapper Service
Provides ultra-simple 1:1 mapping from FMP sectors to internal sector names
"""

from typing import List, Dict, Any
import logging
from services.sector_normalizer import (
    normalize_sector_name,
    log_sector_normalization_warning,
)

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
            "examples": ["Bitcoin Treasury", "AI Transformation", "Defense Spending"],
            "ui_design": "different_styling_vs_regular_sectors",
        }

    def map_fmp_sector(self, fmp_sector: str) -> str:
        """
        Direct 1:1 mapping with 100% confidence and case standardization

        Args:
            fmp_sector: The sector string from FMP data

        Returns:
            Internal sector name (always lowercase) or 'unknown_sector' if not found
        """
        if not fmp_sector:
            return "unknown_sector"

        # Normalize the input sector name (strip whitespace and standardize case)
        normalized_fmp_sector = fmp_sector.strip()

        # Try exact match first
        mapped_sector = self.fmp_mapping.get(normalized_fmp_sector)
        if mapped_sector:
            # Use pure function for final normalization
            final_sector = normalize_sector_name(mapped_sector)
            log_sector_normalization_warning(mapped_sector, final_sector)
            return final_sector

        # Try case-insensitive match for robustness
        for fmp_key, internal_sector in self.fmp_mapping.items():
            if fmp_key.lower() == normalized_fmp_sector.lower():
                # Use pure function for final normalization
                final_sector = normalize_sector_name(internal_sector)
                log_sector_normalization_warning(internal_sector, final_sector)
                return final_sector

        # Log unrecognized sectors for debugging
        logger.warning(
            f"Unrecognized FMP sector: '{fmp_sector}' -> defaulting to 'unknown_sector'"
        )
        return "unknown_sector"

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
        Return theme slot configuration information

        Returns:
            Dict containing theme slot metadata
        """
        return self.theme_slot_config.copy()

    def get_mapping_stats(self) -> Dict[str, Any]:
        """
        Return mapping statistics and confidence metrics

        Returns:
            Dict containing mapping statistics
        """
        return {
            "total_fmp_sectors": len(self.fmp_mapping),
            "total_internal_sectors": len(self.fmp_mapping) + 1,  # +1 for theme slot
            "mapping_confidence": 1.0,  # 100% confidence for 1:1 mapping
            "unknown_sector_fallback": "unknown_sector",
        }
