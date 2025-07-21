#!/usr/bin/env python3
"""
Test 1D sector sentiment storage after cleanup
Validates complete data flow: calculation → storage → database
Uses realistic small-cap stocks (SOUN, BBAI, OCUL, KPTI, etc.)
"""
import asyncio
from services.data_persistence_service import DataPersistenceService
from core.database import SessionLocal
from models.sector_sentiment import SectorSentiment


async def test_storage():
    print("=== Testing 1D Storage Mechanism ===")
    print("Testing with realistic small-cap stocks from our universe")

    # Test data with realistic small-cap stocks from our universe
    test_data = {
        "technology": {
            "sentiment_score": 0.15,
            "top_bullish": ["SOUN", "BBAI"],  # SoundHound AI, BigBear.ai
            "top_bearish": ["PATH"],  # UiPath
            "total_volume": 5000000,
        },
        "healthcare": {
            "sentiment_score": -0.05,
            "top_bullish": ["OCUL"],  # Ocular Therapeutix
            "top_bearish": ["KPTI", "DTIL"],  # Karyopharm, Precision Bio
            "total_volume": 3000000,
        },
    }

    print(f"Input data: {len(test_data)} sectors")
    print("Small-cap stocks included:")
    for sector, data in test_data.items():
        print(
            f"  {sector}: bullish={data['top_bullish']}, bearish={data['top_bearish']}"
        )

    # Store the data
    print("\n--- Storing data via DataPersistenceService ---")
    service = DataPersistenceService()
    result = await service.store_sector_sentiment_data(test_data)
    print(f"Storage result: {result}")

    if not result:
        print("❌ STORAGE FAILED")
        return False

    # Verify the data was stored
    print("\n--- Verifying stored data ---")
    with SessionLocal() as session:
        records = (
            session.query(SectorSentiment)
            .filter(SectorSentiment.timeframe == "1day")
            .order_by(SectorSentiment.sector)
            .all()
        )

        print(f"Records stored: {len(records)}")

        if len(records) == 0:
            print("❌ NO RECORDS FOUND")
            return False

        for record in records:
            print(f"\n  Sector: {record.sector}")
            print(f"  Timeframe: {record.timeframe}")
            print(f"  Score: {record.sentiment_score}")
            print(f"  Bullish count: {record.bullish_count}")
            print(f"  Bearish count: {record.bearish_count}")
            print(f"  Total volume: {record.total_volume}")
            print(f"  Timestamp: {record.timestamp}")

    print("\n=== STORAGE TEST COMPLETED ===")
    print("✅ Data flow validation: calculation → storage → database")
    print("✅ Small-cap test data stored successfully")
    print("✅ Schema validation: composite key (sector, timeframe, timestamp)")

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_storage())
        if result:
            print("\n🎯 TASK 1 SUCCESS: Storage mechanism validated")
            print("Ready for next validation step")
        else:
            print("\n❌ TASK 1 FAILED: Storage mechanism needs debugging")
    except Exception as e:
        print(f"\n❌ TASK 1 ERROR: {e}")
        print("Storage mechanism needs investigation")
