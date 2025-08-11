#!/usr/bin/env python3
"""
Populate stock_prices_1d table using FMP Multiple Company Prices API
Uses the /v3/quote/ endpoint for batch quote retrieval
"""

import asyncio
import logging
from services.fmp_batch_data_service import FMPBatchDataService
from services.universe_builder import UniverseBuilder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def populate_stock_prices_1d():
    """
    Populate stock_prices_1d table using FMP Multiple Company Prices API
    """
    try:
        logger.info('🚀 Starting stock_prices_1d population using FMP Multiple Company Prices API...')
        
        # Initialize services
        universe_builder = UniverseBuilder()
        fmp_batch_service = FMPBatchDataService()
        
        # Step 1: Get FMP screening criteria
        logger.info('📋 Getting FMP screening criteria...')
        screener_criteria = universe_builder.get_fmp_screening_criteria()
        logger.info(f'Screener criteria: {screener_criteria}')
        
        # Step 2: Get universe with price data and store to stock_prices_1d
        logger.info('📊 Retrieving universe with price data using FMP batch quotes (/v3/quote/)...')
        symbols, stock_data_list = await fmp_batch_service.get_universe_with_price_data_and_storage(
            screener_criteria, store_to_db=True
        )
        
        logger.info(f'✅ Successfully populated stock_prices_1d table!')
        logger.info(f'📈 Results: {len(symbols)} symbols, {len(stock_data_list)} price records')
        
        return {
            'status': 'success',
            'symbols_count': len(symbols),
            'price_records_count': len(stock_data_list),
            'api_used': 'FMP Multiple Company Prices API (/v3/quote/)',
            'message': 'stock_prices_1d table populated successfully'
        }
        
    except Exception as e:
        logger.error(f'❌ Error populating stock_prices_1d: {e}')
        return {'status': 'error', 'message': str(e)}

if __name__ == "__main__":
    # Run the population
    result = asyncio.run(populate_stock_prices_1d())
    print(f'\n🎯 Final Result: {result}') 