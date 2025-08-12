#!/usr/bin/env python3
"""
Simple Stock Universe Cleaner - Deletes all data from stock_universe table
"""

import sys
import os
from core.database import SessionLocal
from models.stock_universe import StockUniverse

def clean_stock_universe():
    """Delete all data from stock_universe table"""
    print("🧹 Cleaning stock_universe table...")
    
    with SessionLocal() as session:
        # Get count before deletion
        count_before = session.query(StockUniverse).count()
        print(f"Stocks in table before: {count_before:,}")
        
        # Delete all records
        deleted_count = session.query(StockUniverse).delete()
        session.commit()
        
        print(f"Deleted {deleted_count:,} stocks")
        print("✅ Stock universe table cleaned successfully!")

if __name__ == "__main__":
    clean_stock_universe() 