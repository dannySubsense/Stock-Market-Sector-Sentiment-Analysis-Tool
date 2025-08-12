#!/usr/bin/env python3
"""
Empty all tables in the database
"""

from core.database import engine
from sqlalchemy import text

def empty_all_tables():
    """Empty all tables in the database"""
    try:
        print("🗑️ Emptying all tables in the database...")
        print("=" * 50)
        
        with engine.connect() as conn:
            # Get list of all tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            
            tables = [row.table_name for row in result]
            print(f"📋 Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")
            
            print(f"\n🧹 Starting cleanup...")
            
            # Empty each table
            for table in tables:
                try:
                    # Get count before deletion
                    count_result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                    count_before = count_result.fetchone().count
                    
                    # Delete all records
                    conn.execute(text(f"DELETE FROM {table}"))
                    
                    print(f"✅ Emptied {table}: {count_before:,} records deleted")
                    
                except Exception as e:
                    print(f"❌ Error emptying {table}: {e}")
            
            # Commit all changes
            conn.commit()
            
            print(f"\n🎯 All tables emptied successfully!")
            
            # Verify tables are empty
            print(f"\n🔍 Verification:")
            for table in tables:
                count_result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                count_after = count_result.fetchone().count
                print(f"  {table}: {count_after:,} records remaining")
                
    except Exception as e:
        print(f"❌ Error emptying tables: {e}")

if __name__ == "__main__":
    empty_all_tables() 