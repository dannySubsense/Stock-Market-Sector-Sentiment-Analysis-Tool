#!/usr/bin/env python3
"""
Pure sector normalization functions - Single Responsibility Principle
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_sector_name(sector: Optional[str]) -> str:
    """
    Pure function: normalize sector name to lowercase snake_case

    Args:
        sector: Raw sector string from external source

    Returns:
        Normalized sector name or 'unknown_sector' for invalid input
    """
    if not sector or not isinstance(sector, str):
        return "unknown_sector"

    normalized = sector.strip().lower()
    if not normalized:
        return "unknown_sector"

    return normalized


def log_sector_normalization_warning(original: str, normalized: str) -> None:
    """
    Pure side effect: log sector normalization warnings ONLY when different
    """
    if original != normalized:
        logger.warning(f'Sector normalized: "{original}" -> "{normalized}"')
