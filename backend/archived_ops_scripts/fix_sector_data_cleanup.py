#!/usr/bin/env python3
"""
Sector Data Cleanup Script
Fix existing sector name inconsistencies and standardize all sector names to lowercase
"""
from collections import defaultdict
from core.database import SessionLocal
from models.stock_universe import StockUniverse
from services.sector_mapper import FMPSectorMapper


def fix_sector_name_inconsistencies():
    """Fix sector name case inconsistencies in existing database"""
    print("🔧 SECTOR DATA CLEANUP")
    print("=" * 50)

    # Initialize sector mapper for standardization
    sector_mapper = FMPSectorMapper()

    session = SessionLocal()
    try:
        # Get all stocks with their current sectors
        all_stocks = session.query(StockUniverse).all()

        print(f"📊 Analyzing {len(all_stocks)} stocks...")

        # Track changes
        sector_changes = defaultdict(list)
        updates_made = 0

        for stock in all_stocks:
            original_sector = stock.sector

            # Standardize sector name using our mapper logic
            if original_sector:
                # Apply the same normalization as in sector_mapper
                normalized_sector = original_sector.strip().lower()

                # Map known sector variations to standard names
                sector_standardization = {
                    "technology": "technology",
                    "Technology": "technology",  # Fix the capital T issue
                    "basic_materials": "basic_materials",
                    "communication_services": "communication_services",
                    "consumer_cyclical": "consumer_cyclical",
                    "consumer_defensive": "consumer_defensive",
                    "energy": "energy",
                    "financial_services": "financial_services",
                    "healthcare": "healthcare",
                    "industrials": "industrials",
                    "real_estate": "real_estate",
                    "utilities": "utilities",
                    "unknown_sector": "unknown_sector",
                    "unknown": "unknown_sector",  # Standardize unknown variations
                }

                # Get standardized sector name
                standardized_sector = sector_standardization.get(
                    normalized_sector, normalized_sector  # Keep as-is if not in mapping
                )

                # Update if different
                if original_sector != standardized_sector:
                    sector_changes[f"{original_sector} → {standardized_sector}"].append(
                        stock.symbol
                    )
                    stock.sector = standardized_sector
                    updates_made += 1

        # Show what will be changed
        if sector_changes:
            print(f"\n📝 PROPOSED CHANGES:")
            print("-" * 30)
            for change, symbols in sector_changes.items():
                print(f"{change}: {len(symbols)} stocks")
                if len(symbols) <= 10:
                    print(f"   Stocks: {', '.join(symbols)}")
                else:
                    print(
                        f"   Stocks: {', '.join(symbols[:10])}... (+{len(symbols)-10} more)"
                    )

            # Ask for confirmation
            print(f"\n⚠️  This will update {updates_made} stock records.")
            confirm = input("Proceed with updates? (y/N): ").strip().lower()

            if confirm == "y":
                session.commit()
                print(f"✅ Successfully updated {updates_made} stock records!")

                # Verify the fix
                verify_sector_consistency()
            else:
                session.rollback()
                print("❌ Changes cancelled - no updates made.")
        else:
            print(
                "✅ No sector name inconsistencies found - all sectors are already standardized!"
            )

    except Exception as e:
        session.rollback()
        print(f"❌ Error during cleanup: {e}")
        raise
    finally:
        session.close()


def verify_sector_consistency():
    """Verify that sector names are now consistent"""
    print(f"\n🔍 VERIFICATION: Checking sector consistency...")

    session = SessionLocal()
    try:
        # Get unique sectors
        unique_sectors = session.query(StockUniverse.sector).distinct().all()
        sectors = [sector[0] for sector in unique_sectors if sector[0]]

        print(f"📊 Found {len(sectors)} unique sectors:")
        for sector in sorted(sectors):
            count = (
                session.query(StockUniverse)
                .filter(StockUniverse.sector == sector)
                .count()
            )
            print(f"   • {sector}: {count} stocks")

        # Check for case variations
        sector_lower_map = defaultdict(list)
        for sector in sectors:
            sector_lower_map[sector.lower()].append(sector)

        duplicates_found = False
        for lower_sector, original_sectors in sector_lower_map.items():
            if len(original_sectors) > 1:
                print(
                    f"❌ Still has case variations for '{lower_sector}': {original_sectors}"
                )
                duplicates_found = True

        if not duplicates_found:
            print("✅ All sector names are now consistent!")

    finally:
        session.close()


def show_current_sector_status():
    """Show current sector status before any changes"""
    print("📊 CURRENT SECTOR STATUS:")
    print("-" * 30)

    session = SessionLocal()
    try:
        # Get sector counts
        sector_counts = defaultdict(int)
        all_stocks = session.query(StockUniverse.sector, StockUniverse.is_active).all()

        for sector, is_active in all_stocks:
            if is_active:
                sector_counts[sector] += 1

        for sector, count in sorted(sector_counts.items()):
            print(f"{sector:<25}: {count:>3} stocks")

        # Check for case duplicates
        sector_lower_map = defaultdict(list)
        for sector in sector_counts.keys():
            if sector:
                sector_lower_map[sector.lower()].append(sector)

        print(f"\n🔍 CASE SENSITIVITY ISSUES:")
        issues_found = False
        for lower_sector, original_sectors in sector_lower_map.items():
            if len(original_sectors) > 1:
                print(f"❌ '{lower_sector}' appears as: {original_sectors}")
                issues_found = True

        if not issues_found:
            print("✅ No case sensitivity issues found")

    finally:
        session.close()


if __name__ == "__main__":
    print("🚀 SECTOR DATA STANDARDIZATION TOOL")
    print("=" * 60)
    print("This tool will fix sector name inconsistencies in the database.")
    print("It will standardize all sector names to lowercase and merge duplicates.")
    print()

    # Show current status
    show_current_sector_status()

    print("\n" + "=" * 60)

    # Run the fix
    fix_sector_name_inconsistencies()

    print("\n" + "=" * 60)
    print("✅ SECTOR CLEANUP COMPLETE!")
