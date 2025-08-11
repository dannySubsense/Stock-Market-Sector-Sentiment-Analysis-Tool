from core.database import engine
from models.stock_data import StockPrice1D
from sqlalchemy import text

if __name__ == "__main__":
    print("[INFO] Dropping existing stock_prices_1d table...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS stock_prices_1d CASCADE;"))
        conn.commit()
    
    print("[INFO] Creating stock_prices_1d table with correct schema...")
    StockPrice1D.__table__.create(bind=engine, checkfirst=False)
    print("[INFO] Done. Table is ready.")
