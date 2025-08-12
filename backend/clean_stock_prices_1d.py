#!/usr/bin/env python3
"""
Clean stock_prices_1d table - remove all data
"""

from core.database import engine
from sqlalchemy import text

if __name__ == "__main__":
    print("[INFO] Cleaning stock_prices_1d table...")
    
    with engine.connect() as conn:
        # Get count before
        result = conn.execute(text("SELECT COUNT(*) FROM stock_prices_1d;"))
        count_before = result.fetchone()[0]
        print(f"[INFO] Records before: {count_before}")
        
        # Truncate table
        conn.execute(text("TRUNCATE TABLE stock_prices_1d;"))
        conn.commit()
        
        # Get count after
        result = conn.execute(text("SELECT COUNT(*) FROM stock_prices_1d;"))
        count_after = result.fetchone()[0]
        print(f"[INFO] Records after: {count_after}")
        
    print("[INFO] Table cleaned successfully.") 