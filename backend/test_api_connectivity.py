#!/usr/bin/env python3
"""
Quick API connectivity test
"""
import asyncio
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_api_connections():
    """Test both API connections"""
    print("🔗 Testing API Connections...")
    print("=" * 40)

    try:
        from mcp.fmp_client import get_fmp_client
        from mcp.polygon_client import get_polygon_client

        # Test FMP
        print("📊 Testing FMP API...")
        fmp = get_fmp_client()
        fmp_result = await fmp.test_connection()
        print(f"   Status: {fmp_result['status']}")
        print(f"   Message: {fmp_result['message']}")
        print()

        # Test Polygon
        print("📈 Testing Polygon API...")
        polygon = get_polygon_client()
        polygon_result = await polygon.test_connection()
        print(f"   Status: {polygon_result['status']}")
        print(f"   Message: {polygon_result['message']}")
        print()

        # Summary
        if fmp_result["status"] == "success" and polygon_result["status"] == "success":
            print("✅ Both APIs working correctly!")
            return True
        else:
            print("❌ API connectivity issues detected")
            return False

    except Exception as e:
        print(f"❌ Error testing APIs: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_api_connections())
    sys.exit(0 if success else 1)
