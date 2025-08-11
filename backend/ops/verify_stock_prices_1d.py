#!/usr/bin/env python3
"""
Verify stock_prices_1d table data
"""

from core.database import engine
from sqlalchemy import text

def verify_stock_prices_1d():
    """Verify the stock_prices_1d table data"""
    try:
        with engine.connect() as conn:
            # Count total records
            result = conn.execute(text('SELECT COUNT(*) as count FROM stock_prices_1d'))
            total_count = result.fetchone().count
            print(f'✅ Total records in stock_prices_1d: {total_count:,}')
            
            # Sample records
            result = conn.execute(text("""
                SELECT symbol, name, price, changes_percentage, volume, market_cap 
                FROM stock_prices_1d 
                ORDER BY market_cap DESC 
                LIMIT 5
            """))
            
            print('\n📊 Sample records (by market cap):')
            for row in result:
                print(f'  {row.symbol}: {row.name}')
                print(f'    Price: ${row.price:.2f} ({row.changes_percentage:+.2f}%)')
                print(f'    Volume: {row.volume:,} | Market Cap: ${row.market_cap:,}')
                print()
            
            # Check data quality
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN price > 0 THEN 1 END) as valid_prices,
                    COUNT(CASE WHEN changes_percentage IS NOT NULL THEN 1 END) as valid_changes,
                    COUNT(CASE WHEN volume > 0 THEN 1 END) as valid_volumes
                FROM stock_prices_1d
            """))
            
            quality = result.fetchone()
            print('📈 Data Quality Check:')
            print(f'  Total records: {quality.total:,}')
            print(f'  Valid prices: {quality.valid_prices:,} ({(quality.valid_prices/quality.total)*100:.1f}%)')
            print(f'  Valid changes: {quality.valid_changes:,} ({(quality.valid_changes/quality.total)*100:.1f}%)')
            print(f'  Valid volumes: {quality.valid_volumes:,} ({(quality.valid_volumes/quality.total)*100:.1f}%)')
            
    except Exception as e:
        print(f'❌ Error verifying data: {e}')

if __name__ == "__main__":
    verify_stock_prices_1d() 