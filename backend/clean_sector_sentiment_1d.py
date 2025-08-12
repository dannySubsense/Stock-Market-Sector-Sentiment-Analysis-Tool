#!/usr/bin/env python3
"""
Clean sector_sentiment_1d Table
Empties the sector_sentiment_1d table for fresh pipeline testing
Part of the refactoring: sector_sentiment → sector_sentiment_1d
"""

import sys
import os

# Add both the backend directory and parent directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.dirname(backend_dir))

from core.database import SessionLocal
from models.sector_sentiment_1d import SectorSentiment1D

def clean_sector_sentiment_1d_table():
    """Clean the sector_sentiment_1d table"""
    
    print("=== Cleaning sector_sentiment_1d Table ===")
    print("Preparing for fresh Step 5 testing...")
    
    try:
        with SessionLocal() as db:
            # Count records before cleaning
            count_before = db.query(SectorSentiment1D).count()
            print(f"Records before cleaning: {count_before}")
            
            if count_before == 0:
                print("✅ Table is already empty - no cleaning needed")
                return
            
            # Delete all records
            deleted_count = db.query(SectorSentiment1D).delete()
            db.commit()
            
            # Verify cleaning
            count_after = db.query(SectorSentiment1D).count()
            
            print(f"✅ Successfully deleted {deleted_count} records")
            print(f"✅ Records after cleaning: {count_after}")
            print("✅ sector_sentiment_1d table is now empty")
            print("✅ Ready for fresh Step 5 testing")
            
    except Exception as e:
        print(f"❌ Error cleaning sector_sentiment_1d table: {e}")
        raise

if __name__ == "__main__":
    clean_sector_sentiment_1d_table() 