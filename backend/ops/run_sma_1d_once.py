import sys, asyncio
sys.path.insert(0, 'backend')
from services.sma_1d_pipeline import get_sma_pipeline_1d
from core.database import SessionLocal
from sqlalchemy import text

async def main():
    print('[RUN] Starting 1D SMA pipeline...')
    sma = get_sma_pipeline_1d()
    result = await sma.run()
    print('[RUN] Pipeline completed:', result)

    with SessionLocal() as s:
        counts = {}
        for table in ['stock_universe','stock_prices_1d','sector_sentiment_1d','sector_gappers_1d']:
            c = s.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            counts[table] = c
        print('[COUNTS]', counts)

if __name__ == '__main__':
    asyncio.run(main())
