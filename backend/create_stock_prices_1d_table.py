from core.database import engine
from models.stock_data import StockPrice1D

if __name__ == "__main__":
    print("[INFO] Creating stock_prices_1d table if it does not exist...")
    StockPrice1D.__table__.create(bind=engine, checkfirst=True)
    print("[INFO] Done. Table is ready.")
