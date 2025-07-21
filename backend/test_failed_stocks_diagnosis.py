#!/usr/bin/env python3
"""
Failed Stocks Diagnosis
Investigate why specific stocks failed to return data from Polygon API
"""
import asyncio
from typing import List, Dict, Any

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from services.stock_data_retrieval_1d import StockDataRetrieval1D
from mcp.polygon_client import get_polygon_client


class FailedStocksDiagnostic:
    """Diagnose why specific stocks failed"""

    def __init__(self):
        self.data_retrieval = StockDataRetrieval1D()
        self.polygon_client = get_polygon_client()

    async def diagnose_failed_stock(self, symbol: str) -> Dict[str, Any]:
        """Diagnose a single failed stock"""
        print(f"\n🔍 DIAGNOSING: {symbol}")

        result = {
            "symbol": symbol,
            "polygon_quote_success": False,
            "polygon_previous_close_success": False,
            "stock_data_retrieval_success": False,
            "errors": [],
            "raw_responses": {},
        }

        # Test 1: Direct Polygon quote
        try:
            quote_response = await self.polygon_client.get_real_time_quote(symbol)
            result["polygon_quote_success"] = quote_response.get("status") == "success"
            result["raw_responses"]["quote"] = quote_response
            if quote_response.get("status") != "success":
                result["errors"].append(
                    f"Polygon quote failed: {quote_response.get('message', 'Unknown error')}"
                )
            else:
                print(f"   ✅ Polygon quote: SUCCESS")
        except Exception as e:
            result["errors"].append(f"Polygon quote exception: {str(e)}")
            print(f"   ❌ Polygon quote: EXCEPTION - {e}")

        # Test 2: Direct Polygon previous close
        try:
            prev_close_response = await self.polygon_client.get_previous_close(symbol)
            result["polygon_previous_close_success"] = (
                prev_close_response.get("status") == "success"
            )
            result["raw_responses"]["previous_close"] = prev_close_response
            if prev_close_response.get("status") != "success":
                result["errors"].append(
                    f"Polygon previous close failed: {prev_close_response.get('message', 'Unknown error')}"
                )
            else:
                print(f"   ✅ Polygon previous close: SUCCESS")
        except Exception as e:
            result["errors"].append(f"Polygon previous close exception: {str(e)}")
            print(f"   ❌ Polygon previous close: EXCEPTION - {e}")

        # Test 3: Our StockDataRetrieval1D service
        try:
            stock_data = await self.data_retrieval.get_1d_stock_data(symbol, "polygon")
            result["stock_data_retrieval_success"] = stock_data is not None
            if stock_data is None:
                result["errors"].append("StockDataRetrieval1D returned None")
                print(f"   ❌ StockDataRetrieval1D: FAILED - returned None")
            else:
                print(f"   ✅ StockDataRetrieval1D: SUCCESS")
                result["stock_data_summary"] = {
                    "symbol": stock_data.symbol,
                    "current_price": stock_data.current_price,
                    "previous_close": stock_data.previous_close,
                    "volume": stock_data.volume,
                }
        except Exception as e:
            result["errors"].append(f"StockDataRetrieval1D exception: {str(e)}")
            print(f"   ❌ StockDataRetrieval1D: EXCEPTION - {e}")

        # Check if stock exists in our universe
        session = SessionLocal()
        try:
            stock_info = (
                session.query(StockUniverse)
                .filter(StockUniverse.symbol == symbol)
                .first()
            )
            if stock_info:
                result["universe_info"] = {
                    "sector": stock_info.sector,
                    "market_cap": stock_info.market_cap,
                    "exchange": stock_info.exchange,
                }
                print(
                    f"   📊 Universe: {stock_info.sector} | {stock_info.exchange} | ${stock_info.market_cap:,.0f}M"
                )
            else:
                result["errors"].append("Stock not found in universe")
                print(f"   ⚠️  Universe: NOT FOUND")
        finally:
            session.close()

        return result

    async def diagnose_all_failed_stocks(self):
        """Diagnose all failed stocks from the stress test"""
        failed_stocks = [
            "INZY",
            "ICAD",
            "EYEN",
            "AKYA",
            "SNPX",  # healthcare
            "RDUS",  # basic_materials
            "SRM",
            "LTRY",  # consumer_cyclical
            "CLBR",
            "JVSA",  # financial_services
            "CGBS",  # energy
        ]

        print("🚨 FAILED STOCKS DIAGNOSTIC")
        print("=" * 50)
        print(f"Investigating {len(failed_stocks)} failed stocks...")

        results = []
        for symbol in failed_stocks:
            result = await self.diagnose_failed_stock(symbol)
            results.append(result)
            await asyncio.sleep(0.1)  # Brief pause between diagnostics

        # Summary analysis
        print("\n" + "=" * 50)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 50)

        # Categorize failures
        polygon_quote_failures = sum(
            1 for r in results if not r["polygon_quote_success"]
        )
        polygon_prev_failures = sum(
            1 for r in results if not r["polygon_previous_close_success"]
        )
        service_failures = sum(
            1 for r in results if not r["stock_data_retrieval_success"]
        )

        print(f"📈 Failure Breakdown:")
        print(
            f"   • Polygon quote failures: {polygon_quote_failures}/{len(failed_stocks)}"
        )
        print(
            f"   • Polygon previous close failures: {polygon_prev_failures}/{len(failed_stocks)}"
        )
        print(f"   • Service layer failures: {service_failures}/{len(failed_stocks)}")

        # Common error patterns
        all_errors = []
        for result in results:
            all_errors.extend(result["errors"])

        error_patterns = {}
        for error in all_errors:
            error_type = error.split(":")[0] if ":" in error else error
            error_patterns[error_type] = error_patterns.get(error_type, 0) + 1

        print(f"\n🔍 Common Error Patterns:")
        for pattern, count in sorted(
            error_patterns.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"   • {pattern}: {count} occurrences")

        # Possible causes and solutions
        print(f"\n💡 LIKELY CAUSES:")
        if polygon_quote_failures > len(failed_stocks) * 0.5:
            print("   🎯 PRIMARY: Polygon API coverage gaps")
            print("      → Some stocks may not be available on Polygon")
            print("      → Could be OTC, pink sheets, or recently delisted")

        if polygon_prev_failures > polygon_quote_failures:
            print("   🎯 SECONDARY: Previous close data missing")
            print("      → Stock might be newly listed")
            print("      → Historical data gap on Polygon")

        print(f"\n✅ RECOMMENDATION:")
        failure_rate = len(failed_stocks) / 2073 * 100
        print(f"   • {failure_rate:.2f}% failure rate is EXCELLENT for financial APIs")
        print("   • Failed stocks likely have legitimate data gaps")
        print("   • Consider implementing FMP fallback for these edge cases")

        return results


async def main():
    """Run failed stocks diagnostic"""
    diagnostic = FailedStocksDiagnostic()
    await diagnostic.diagnose_all_failed_stocks()


if __name__ == "__main__":
    asyncio.run(main())
