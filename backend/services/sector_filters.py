"""
Sector Filters for SMA Calculation

Defines filter structures for gap, volume, and price filtering
in the simplified SMA sector performance calculation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class GapFilter:
    """Filter for gap percentage ranges"""

    min_gap: float = -500.0  # -500% minimum gap (include losses)
    max_gap: float = 500.0  # 500% maximum gap


@dataclass
class VolumeFilter:
    """Filter for volume ranges"""

    min_volume: int = 100_000  # 100K minimum volume (more inclusive for small caps)
    max_volume: Optional[int] = None  # No maximum


@dataclass
class PriceFilter:
    """Filter for price ranges"""

    min_price: float = 1.0  # $1 minimum price
    max_price: Optional[float] = None  # No maximum


@dataclass
class SectorFilters:
    """Combined filters for sector data filtering"""

    gap: GapFilter = field(default_factory=GapFilter)
    volume: VolumeFilter = field(default_factory=VolumeFilter)
    price: PriceFilter = field(default_factory=PriceFilter)

    def to_sql_params(self) -> Dict[str, Any]:
        """Convert filters to SQL parameters for database query"""
        params = {}

        # Gap filter parameters
        params["min_gap"] = self.gap.min_gap
        params["max_gap"] = self.gap.max_gap

        # Volume filter parameters
        params["min_volume"] = self.volume.min_volume
        if self.volume.max_volume:
            params["max_volume"] = self.volume.max_volume

        # Price filter parameters
        params["min_price"] = self.price.min_price
        if self.price.max_price:
            params["max_price"] = self.price.max_price

        return params
