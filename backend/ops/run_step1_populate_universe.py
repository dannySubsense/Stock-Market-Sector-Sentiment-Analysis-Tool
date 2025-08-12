import sys, asyncio
sys.path.insert(0, 'backend')
from services.universe_builder import UniverseBuilder
from core.database import SessionLocal
from sqlalchemy import text

async def main():
    print('[STEP1] Building daily universe via FMP...')
    ub = UniverseBuilder()
    res = await ub.build_daily_universe()
    print('[STEP1] Universe result:', res)
    with SessionLocal() as s:
        cnt = s.execute(text('SELECT COUNT(*) FROM stock_universe')).scalar()
        print('[STEP1] stock_universe count:', cnt)

if __name__ == '__main__':
    asyncio.run(main())
