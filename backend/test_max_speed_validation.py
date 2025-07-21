#!/usr/bin/env python3
"""
Step 5: MAXIMUM SPEED Validation Test
Goal: Find absolute fastest processing speed with Polygon API
"""
import asyncio
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from services.stock_data_retrieval_1d import StockDataRetrieval1D


class MaxSpeedValidator:
    """Test maximum achievable speed with Polygon API"""

    def __init__(self):
        self.data_retrieval = StockDataRetrieval1D()

    async def concurrent_stock_batch(
        self, symbols: List[str], concurrent_limit: int = 10
    ) -> Dict[str, Any]:
        """Process stocks with concurrent API calls"""
        print(
            f"🚀 Processing {len(symbols)} stocks with {concurrent_limit} concurrent calls"
        )

        start_time = time.time()
        successful_stocks = []
        failed_stocks = []

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def fetch_single_stock(symbol: str) -> bool:
            async with semaphore:
                try:
                    data = await self.data_retrieval.get_1d_stock_data(
                        symbol, "polygon"
                    )
                    if data:
                        successful_stocks.append(symbol)
                        return True
                    else:
                        failed_stocks.append(symbol)
                        return False
                except Exception as e:
                    failed_stocks.append(symbol)
                    return False

        # Execute all requests concurrently
        tasks = [fetch_single_stock(symbol) for symbol in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)

        elapsed_time = time.time() - start_time

        return {
            "total_stocks": len(symbols),
            "successful": len(successful_stocks),
            "failed": len(failed_stocks),
            "elapsed_time": elapsed_time,
            "stocks_per_minute": (
                (len(symbols) / elapsed_time) * 60 if elapsed_time > 0 else 0
            ),
            "success_rate": (
                len(successful_stocks) / len(symbols) * 100 if symbols else 0
            ),
        }

    async def test_speed_configurations(self) -> None:
        """Test different concurrent configurations to find optimal speed"""

        # Get sample stocks
        session = SessionLocal()
        try:
            sample_stocks = (
                session.query(StockUniverse.symbol)
                .filter(StockUniverse.sector != "unknown")
                .limit(100)
                .all()
            )
            symbols = [stock.symbol for stock in sample_stocks]
        finally:
            session.close()

        print(f"📊 Testing speed configurations with {len(symbols)} stocks\n")

        configurations = [
            {"concurrent": 5, "name": "Conservative (5 concurrent)"},
            {"concurrent": 10, "name": "Moderate (10 concurrent)"},
            {"concurrent": 15, "name": "Aggressive (15 concurrent)"},
            {"concurrent": 20, "name": "Maximum (20 concurrent)"},
        ]

        results = []

        for config in configurations:
            print(f"🧪 Testing: {config['name']}")

            result = await self.concurrent_stock_batch(
                symbols[:50],  # Use 50 stocks for speed test
                concurrent_limit=config["concurrent"],
            )

            result["configuration"] = config["name"]
            results.append(result)

            print(f"   ✅ {result['successful']}/{result['total_stocks']} stocks")
            print(f"   ⚡ {result['stocks_per_minute']:.0f} stocks/minute")
            print(f"   ⏱️  {result['elapsed_time']:.2f} seconds")
            print(f"   📈 {result['success_rate']:.1f}% success rate\n")

            # Brief pause between tests
            await asyncio.sleep(2)

        # Find best configuration
        best_config = max(results, key=lambda x: x["stocks_per_minute"])

        print("🏆 OPTIMAL CONFIGURATION FOUND:")
        print(f"   🥇 Best: {best_config['configuration']}")
        print(f"   ⚡ Speed: {best_config['stocks_per_minute']:.0f} stocks/minute")
        print(f"   📈 Success: {best_config['success_rate']:.1f}%")

        # Project full universe time
        full_universe_minutes = 2058 / best_config["stocks_per_minute"]
        print(f"   🎯 Full 2,058 stocks: {full_universe_minutes:.1f} minutes")

        return best_config


async def main():
    """Run maximum speed validation"""
    print("🚀 MAXIMUM SPEED VALIDATION TEST")
    print("=" * 50)

    validator = MaxSpeedValidator()
    best_config = await validator.test_speed_configurations()

    print("\n" + "=" * 50)
    print("✅ SPEED OPTIMIZATION COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
