#!/usr/bin/env python3
"""
Sector Duplication Investigation
Find out why Technology sector appears twice in our stress test results
"""
from collections import defaultdict, Counter
from core.database import SessionLocal
from models.stock_universe import StockUniverse


def investigate_sector_duplication():
    """Investigate sector naming and duplication issues"""
    print("🔍 SECTOR DUPLICATION INVESTIGATION")
    print("=" * 50)

    session = SessionLocal()
    try:
        # Get all stocks with their sectors
        all_stocks = (
            session.query(
                StockUniverse.symbol, StockUniverse.sector, StockUniverse.is_active
            )
            .filter(StockUniverse.sector != "unknown")
            .all()
        )

        print(f"📊 Total stocks analyzed: {len(all_stocks)}")

        # Group by sector and count
        sector_counts = defaultdict(list)
        sector_variations = Counter()

        for stock in all_stocks:
            sector_counts[stock.sector].append(
                {"symbol": stock.symbol, "is_active": stock.is_active}
            )
            sector_variations[stock.sector] += 1

        print(f"\n📈 SECTOR BREAKDOWN:")
        print("-" * 30)

        for sector, stocks in sorted(sector_counts.items()):
            active_count = sum(1 for s in stocks if s["is_active"])
            total_count = len(stocks)
            print(f"{sector:<25}: {active_count:>3}/{total_count:<3} active")

        # Look for technology variations specifically
        print(f"\n🔍 TECHNOLOGY SECTOR ANALYSIS:")
        print("-" * 40)

        tech_variations = [
            sector for sector in sector_counts.keys() if "tech" in sector.lower()
        ]

        if tech_variations:
            print(f"Found {len(tech_variations)} technology-related sectors:")
            for tech_sector in tech_variations:
                stocks = sector_counts[tech_sector]
                active_count = sum(1 for s in stocks if s["is_active"])
                total_count = len(stocks)
                print(f"  • {tech_sector}: {active_count}/{total_count} stocks")

                # Show sample stocks
                sample_stocks = [s["symbol"] for s in stocks[:5] if s["is_active"]]
                print(f"    Sample: {', '.join(sample_stocks)}")
        else:
            print("No technology sectors found!")

        # Look for exact duplicates
        print(f"\n⚠️  POTENTIAL ISSUES:")
        print("-" * 30)

        # Check for case variations
        sector_lower_map = defaultdict(list)
        for sector in sector_counts.keys():
            sector_lower_map[sector.lower()].append(sector)

        duplicates_found = False
        for lower_sector, original_sectors in sector_lower_map.items():
            if len(original_sectors) > 1:
                print(f"❌ Case variations for '{lower_sector}': {original_sectors}")
                duplicates_found = True

        # Check for suspicious sector names
        suspicious_sectors = []
        for sector in sector_counts.keys():
            if any(char in sector for char in ["_", "-", " ", "."]):
                suspicious_sectors.append(sector)

        if suspicious_sectors:
            print(f"🚨 Sectors with unusual characters: {suspicious_sectors}")
            duplicates_found = True

        # Check for very small sectors (might be data quality issues)
        small_sectors = []
        for sector, stocks in sector_counts.items():
            active_count = sum(1 for s in stocks if s["is_active"])
            if 1 <= active_count <= 5:  # Very small sectors
                small_sectors.append((sector, active_count))

        if small_sectors:
            print(f"🔍 Very small sectors (1-5 stocks):")
            for sector, count in small_sectors:
                print(f"  • {sector}: {count} stocks")
                # Show which stocks
                stocks = sector_counts[sector]
                symbols = [s["symbol"] for s in stocks if s["is_active"]]
                print(f"    Stocks: {', '.join(symbols)}")
            duplicates_found = True

        if not duplicates_found:
            print("✅ No obvious duplication issues found")

        # Show expected sectors vs actual
        print(f"\n📋 EXPECTED vs ACTUAL SECTORS:")
        print("-" * 40)

        expected_sectors = {
            "technology",
            "healthcare",
            "energy",
            "financial_services",
            "consumer_cyclical",
            "consumer_defensive",
            "industrials",
            "basic_materials",
            "real_estate",
            "communication_services",
            "utilities",
        }

        actual_sectors = set(sector_counts.keys())

        print(f"Expected: {sorted(expected_sectors)}")
        print(f"Actual: {sorted(actual_sectors)}")

        missing = expected_sectors - actual_sectors
        extra = actual_sectors - expected_sectors

        if missing:
            print(f"❌ Missing expected sectors: {sorted(missing)}")
        if extra:
            print(f"⚠️  Extra/unexpected sectors: {sorted(extra)}")

        return sector_counts

    finally:
        session.close()


def investigate_specific_tech_stocks():
    """Look at specific technology stocks to understand the duplication"""
    print(f"\n🔍 DETAILED TECHNOLOGY STOCK ANALYSIS:")
    print("=" * 50)

    session = SessionLocal()
    try:
        # Get all stocks that might be technology
        tech_stocks = (
            session.query(
                StockUniverse.symbol,
                StockUniverse.sector,
                StockUniverse.company_name,
                StockUniverse.market_cap,
                StockUniverse.exchange,
                StockUniverse.is_active,
            )
            .filter(StockUniverse.sector.like("%tech%"))
            .order_by(StockUniverse.sector, StockUniverse.symbol)
            .all()
        )

        print(f"Found {len(tech_stocks)} technology-related stocks")

        # Group by exact sector name
        by_sector = defaultdict(list)
        for stock in tech_stocks:
            by_sector[stock.sector].append(stock)

        for sector_name, stocks in by_sector.items():
            active_stocks = [s for s in stocks if s.is_active]
            print(f"\n📊 SECTOR: {sector_name}")
            print(f"   Active stocks: {len(active_stocks)}/{len(stocks)}")

            # Show first few stocks for verification
            for stock in active_stocks[:10]:  # First 10 active stocks
                print(
                    f"   • {stock.symbol:<6} | {stock.company_name:<30} | ${stock.market_cap:>8,.0f}M | {stock.exchange}"
                )

            if len(active_stocks) > 10:
                print(f"   ... and {len(active_stocks) - 10} more stocks")

    finally:
        session.close()


if __name__ == "__main__":
    sector_counts = investigate_sector_duplication()
    investigate_specific_tech_stocks()

    print(f"\n💡 RECOMMENDATIONS:")
    print("=" * 50)
    print("1. Check if there are case-sensitive duplicates")
    print("2. Verify sector standardization in universe builder")
    print("3. Look for trailing spaces or special characters")
    print("4. Ensure consistent sector mapping from FMP")
    print("5. Consider data cleanup/normalization step")
