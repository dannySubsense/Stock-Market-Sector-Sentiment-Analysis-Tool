#!/usr/bin/env python3
"""
Test the simplified freshness service
"""
from services.data_freshness_service import get_freshness_service
from core.database import SessionLocal


def test_freshness():
    print("=== Testing Simplified Freshness Service ===")

    service = get_freshness_service()
    print(f"Staleness threshold: {service.staleness_threshold}")

    with SessionLocal() as db:
        results = service.get_sector_sentiment_with_freshness(db)
        print(f"\nResults: {len(results)} sectors found")

        for record, is_stale in results:
            age_info = service.get_data_age_info(record.timestamp)
            print(f"{record.sector}: {record.sentiment_score}")
            print(f"  Age: {age_info['age_minutes']} minutes")
            print(f"  Stale: {is_stale}")
            print(f"  Status: {age_info['status']}")
            print()


if __name__ == "__main__":
    test_freshness()
