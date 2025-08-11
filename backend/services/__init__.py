# Re-export validated simple SMA services under sma_* aliases for clarity
from .simple_sector_calculator import SectorCalculator as SMASectorCalculator  # noqa: F401
from .sector_data_service import SectorDataService as SMADataService  # noqa: F401
from .sector_filters import SectorFilters as SMAFilters  # noqa: F401
"""
Services package for Market Sector Sentiment Analysis Tool
- Keep imports minimal to avoid side effects when importing the package
- Submodules (e.g., analysis_scheduler, universe_builder) should be imported directly
"""

__all__ = [
    "SMASectorCalculator",
    "SMADataService",
    "SMAFilters",
]
