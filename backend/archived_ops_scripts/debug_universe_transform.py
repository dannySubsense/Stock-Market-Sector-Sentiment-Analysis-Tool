#!/usr/bin/env python3
"""
Debug script to test _transform_fmp_to_database_format behavior
"""
from unittest.mock import patch
from services.universe_builder import UniverseBuilder


def test_sector_handling():
    """Test how the universe builder handles different sector values"""
    with patch("services.universe_builder.get_polygon_client"), patch(
        "services.universe_builder.get_fmp_client"
    ), patch("services.universe_builder.FMPSectorMapper"), patch(
        "services.universe_builder.get_weight_for_sector", return_value=1.0
    ):

        universe_builder = UniverseBuilder()

        test_cases = [
            {
                "name": "None sector",
                "input": {
                    "symbol": "TEST1",
                    "companyName": "Test 1",
                    "exchange": "NYSE",
                    "marketCap": 100000000,
                    "volume": 1000000,
                    "price": 10.0,
                    "sector": None,
                    "original_fmp_sector": "",
                },
            },
            {
                "name": "Empty string sector",
                "input": {
                    "symbol": "TEST2",
                    "companyName": "Test 2",
                    "exchange": "NYSE",
                    "marketCap": 100000000,
                    "volume": 1000000,
                    "price": 10.0,
                    "sector": "",
                    "original_fmp_sector": "",
                },
            },
            {
                "name": "Missing sector key",
                "input": {
                    "symbol": "TEST3",
                    "companyName": "Test 3",
                    "exchange": "NYSE",
                    "marketCap": 100000000,
                    "volume": 1000000,
                    "price": 10.0,
                    # No sector key at all
                    "original_fmp_sector": "",
                },
            },
            {
                "name": "Whitespace sector",
                "input": {
                    "symbol": "TEST4",
                    "companyName": "Test 4",
                    "exchange": "NYSE",
                    "marketCap": 100000000,
                    "volume": 1000000,
                    "price": 10.0,
                    "sector": "   ",
                    "original_fmp_sector": "",
                },
            },
        ]

        for case in test_cases:
            print(f"\n=== {case['name']} ===")
            print(f"Input sector: {repr(case['input'].get('sector', 'KEY_MISSING'))}")

            result = universe_builder._transform_fmp_to_database_format(case["input"])
            print(f"Output sector: {repr(result['sector'])}")
            print(f"Sector type: {type(result['sector'])}")


if __name__ == "__main__":
    test_sector_handling()
