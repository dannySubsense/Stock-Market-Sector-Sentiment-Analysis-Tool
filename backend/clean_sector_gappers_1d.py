#!/usr/bin/env python3
"""
Clean sector_gappers_1d Table

This script clears all records from the sector_gappers_1d table
to prepare for fresh testing of the separated gapper architecture.
"""

import sys
import os
import logging
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(__file__))

from core.database import SessionLocal
import sqlalchemy

logger = logging.getLogger(__name__)


def clean_sector_gappers_1d():
    """Clean all records from sector_gappers_1d table"""
    
    print("=== Cleaning sector_gappers_1d Table ===")
    print("Preparing for fresh gapper testing...")
    
    try:
        with SessionLocal() as db:
            # Count records before cleaning
            result = db.execute(sqlalchemy.text("SELECT COUNT(*) FROM sector_gappers_1d"))
            count_before = result.fetchone()[0]
            print(f"Records before cleaning: {count_before}")
            
            # Delete all records
            db.execute(sqlalchemy.text("DELETE FROM sector_gappers_1d"))
            db.commit()
            
            # Count records after cleaning
            result = db.execute(sqlalchemy.text("SELECT COUNT(*) FROM sector_gappers_1d"))
            count_after = result.fetchone()[0]
            
            print(f"✅ Successfully deleted {count_before} records")
            print(f"✅ Records after cleaning: {count_after}")
            print("✅ sector_gappers_1d table is now empty")
            print("✅ Ready for fresh gapper testing")
            
    except Exception as e:
        logger.error(f"Error cleaning sector_gappers_1d table: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    clean_sector_gappers_1d() 