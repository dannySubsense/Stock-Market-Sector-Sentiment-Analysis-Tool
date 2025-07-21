"""
Persistence Interface - Separation of Concerns for Database Operations
Enables dependency injection and clean testing of business logic
"""

from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PersistenceLayer(Protocol):
    """
    Protocol for persistence operations
    Enables dependency injection and testing with mock implementations
    """

    async def store_stock_data(self, stock_data_list: List) -> bool:
        """Store stock price/volume data"""
        ...

    async def store_sector_sentiment(
        self, sector_results: Dict[str, Any], metadata: Optional[Dict] = None
    ) -> bool:
        """Store sector sentiment analysis results"""
        ...

    async def store_iwm_benchmark(self, iwm_data) -> bool:
        """Store IWM benchmark data"""
        ...


class NullPersistence:
    """
    No-op persistence implementation for testing and development
    Allows business logic to run without database dependencies
    """

    async def store_stock_data(self, stock_data_list: List) -> bool:
        """No-op stock data storage"""
        count = len(stock_data_list) if stock_data_list is not None else 0
        logger.debug(f"NullPersistence: Would store {count} stock records")
        return True

    async def store_sector_sentiment(
        self, sector_results: Dict[str, Any], metadata: Optional[Dict] = None
    ) -> bool:
        """No-op sector sentiment storage"""
        count = len(sector_results) if sector_results is not None else 0
        logger.debug(f"NullPersistence: Would store sentiment for {count} sectors")
        return True

    async def store_iwm_benchmark(self, iwm_data) -> bool:
        """No-op IWM benchmark storage"""
        logger.debug(f"NullPersistence: Would store IWM benchmark data")
        return True


class DatabasePersistence:
    """
    Real database persistence implementation
    Wraps the existing DataPersistenceService
    """

    def __init__(self):
        from services.data_persistence_service import get_persistence_service

        self._persistence_service = get_persistence_service()

    async def store_stock_data(self, stock_data_list: List) -> bool:
        """Store stock data using real database service"""
        try:
            return await self._persistence_service.store_stock_price_data(
                stock_data_list
            )
        except Exception as e:
            logger.error(f"Database persistence failed for stock data: {e}")
            return False

    async def store_sector_sentiment(
        self, sector_results: Dict[str, Any], metadata: Optional[Dict] = None
    ) -> bool:
        """Store sector sentiment using real database service"""
        try:
            return await self._persistence_service.store_sector_sentiment_data(
                sector_results, metadata
            )
        except Exception as e:
            logger.error(f"Database persistence failed for sector sentiment: {e}")
            return False

    async def store_iwm_benchmark(self, iwm_data) -> bool:
        """Store IWM benchmark using real database service"""
        try:
            return await self._persistence_service.store_iwm_benchmark_data(iwm_data)
        except Exception as e:
            logger.error(f"Database persistence failed for IWM benchmark: {e}")
            return False


def get_persistence_layer(enable_database: bool = True) -> PersistenceLayer:
    """
    Factory function for persistence layer

    Args:
        enable_database: If True, use real database. If False, use null persistence.

    Returns:
        Appropriate persistence implementation
    """
    if enable_database:
        return DatabasePersistence()
    else:
        return NullPersistence()
