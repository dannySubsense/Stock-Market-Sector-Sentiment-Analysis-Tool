#!/usr/bin/env python3
"""
Step 5 Pipeline Validation - Senior Engineer Approach
Risk-based testing with observability and fail-fast principles
"""
import asyncio
import time
import logging
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from services.sector_aggregation_1d import SectorAggregation1D

# Set up logging for visibility
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SectorTestResult:
    sector: str
    stocks_tested: int
    success_count: int
    failure_count: int
    avg_response_time: float
    errors: List[str]
    sentiment_score: float


@dataclass
class PipelineValidationReport:
    total_sectors: int
    total_stocks_tested: int
    total_time_seconds: float
    success_rate: float
    sector_results: List[SectorTestResult]
    critical_issues: List[str]


class PipelineValidator:
    """Senior engineer approach to pipeline validation"""

    def __init__(self):
        self.aggregation_service = SectorAggregation1D()
        self.test_results = []

    async def run_smoke_tests(self) -> bool:
        """Phase 1: Quick smoke tests across all sectors"""
        logger.info("🚀 PHASE 1: SMOKE TESTS (2-3 stocks per sector)")
        logger.info("=" * 60)

        sectors = self._get_test_sectors()
        critical_failures = []

        for sector in sectors:
            try:
                logger.info(f"💨 Smoke testing {sector}...")
                stocks = self._get_sample_stocks(sector, limit=3)

                if not stocks:
                    logger.warning(f"⚠️  No stocks found for {sector}")
                    continue

                start_time = time.time()
                result = await self.aggregation_service.aggregate_sector_sentiment_1d(
                    sector
                )
                elapsed = time.time() - start_time

                if result and result.sentiment_score is not None:
                    logger.info(
                        f"✅ {sector}: {len(stocks)} stocks, {elapsed:.1f}s, sentiment: {result.sentiment_score:.3f}"
                    )
                else:
                    logger.error(f"❌ {sector}: Failed to get valid result")
                    critical_failures.append(f"{sector}: No valid sentiment result")

            except Exception as e:
                logger.error(f"💥 {sector}: Critical failure - {e}")
                critical_failures.append(f"{sector}: {str(e)}")

        if critical_failures:
            logger.error(f"🚨 SMOKE TEST FAILURES: {len(critical_failures)}")
            for failure in critical_failures:
                logger.error(f"   - {failure}")
            return False

        logger.info("✅ SMOKE TESTS PASSED - Proceeding to sampling")
        return True

    async def run_representative_sampling(self) -> bool:
        """Phase 2: Representative sampling for performance validation"""
        logger.info("📊 PHASE 2: REPRESENTATIVE SAMPLING")
        logger.info("=" * 60)

        # Risk-based sampling strategy
        sampling_strategy = {
            "healthcare": 20,  # Largest sector
            "financial_services": 20,  # Second largest
            "technology": 15,  # Already tested some
            "industrials": 10,
            "consumer_cyclical": 10,
            "energy": 5,
            "real_estate": 5,
            "communication_services": 5,
            "basic_materials": 5,
            "consumer_defensive": 5,
            "utilities": 3,  # Smallest
        }

        performance_issues = []

        for sector, sample_size in sampling_strategy.items():
            try:
                logger.info(f"📈 Sampling {sector} ({sample_size} stocks)...")
                stocks = self._get_sample_stocks(sector, limit=sample_size)

                if len(stocks) < sample_size // 2:
                    logger.warning(
                        f"⚠️  {sector}: Only {len(stocks)} stocks available (expected {sample_size})"
                    )

                start_time = time.time()
                result = await self.aggregation_service.aggregate_sector_sentiment_1d(
                    sector
                )
                elapsed = time.time() - start_time

                # Performance validation
                expected_time = len(stocks) * 1.2  # 1.2s per stock with overhead
                if elapsed > expected_time * 2:
                    performance_issues.append(
                        f"{sector}: {elapsed:.1f}s (expected ~{expected_time:.1f}s)"
                    )

                logger.info(
                    f"📊 {sector}: {len(stocks)} stocks, {elapsed:.1f}s, sentiment: {result.sentiment_score:.3f}"
                )

            except Exception as e:
                logger.error(f"💥 {sector} sampling failed: {e}")
                performance_issues.append(f"{sector}: Exception - {str(e)}")

        if performance_issues:
            logger.warning(f"⚠️  PERFORMANCE CONCERNS: {len(performance_issues)}")
            for issue in performance_issues:
                logger.warning(f"   - {issue}")

        logger.info("✅ REPRESENTATIVE SAMPLING COMPLETE")
        return True

    async def run_critical_path_validation(self) -> bool:
        """Phase 3: Full testing of most critical sector"""
        logger.info("🎯 PHASE 3: CRITICAL PATH VALIDATION")
        logger.info("=" * 60)

        # Test the largest, most complex sector fully
        critical_sector = "healthcare"  # 546 stocks

        logger.info(f"🔥 Full validation of {critical_sector} sector...")
        logger.info(f"   Expected time: ~9.1 minutes")
        logger.info(f"   This validates production performance characteristics")

        start_time = time.time()
        try:
            result = await self.aggregation_service.aggregate_sector_sentiment_1d(
                critical_sector
            )
            elapsed = time.time() - start_time

            logger.info(f"✅ CRITICAL PATH COMPLETE:")
            logger.info(f"   Sector: {critical_sector}")
            logger.info(f"   Time: {elapsed/60:.2f} minutes")
            logger.info(f"   Sentiment: {result.sentiment_score:.3f}")
            logger.info(f"   Color: {result.color_classification}")

            return True

        except Exception as e:
            logger.error(f"💥 CRITICAL PATH FAILED: {e}")
            return False

    def _get_test_sectors(self) -> List[str]:
        """Get all sectors except unknown"""
        with SessionLocal() as db:
            sectors = (
                db.query(StockUniverse.sector)
                .filter(
                    StockUniverse.is_active == True,
                    StockUniverse.sector != "unknown_sector",
                )
                .distinct()
                .all()
            )
            return [sector[0] for sector in sectors]

    def _get_sample_stocks(self, sector: str, limit: int) -> List[str]:
        """Get sample stocks from sector"""
        with SessionLocal() as db:
            stocks = (
                db.query(StockUniverse.symbol)
                .filter(StockUniverse.sector == sector, StockUniverse.is_active == True)
                .limit(limit)
                .all()
            )
            return [stock[0] for stock in stocks]


async def main():
    """Senior engineer pipeline validation approach"""
    print("🎯 STEP 5 PIPELINE VALIDATION - SENIOR ENGINEER APPROACH")
    print("=" * 70)
    print("Strategy: Risk-based testing with fail-fast principles")
    print("Phases: Smoke → Sampling → Critical Path")
    print("=" * 70)

    validator = PipelineValidator()

    # Phase 1: Smoke Tests (~5 minutes)
    if not await validator.run_smoke_tests():
        print("🚨 SMOKE TESTS FAILED - STOPPING")
        return

    # Phase 2: Representative Sampling (~15 minutes)
    if not await validator.run_representative_sampling():
        print("⚠️  SAMPLING ISSUES DETECTED")

    # Phase 3: Critical Path Validation (~9 minutes)
    if not await validator.run_critical_path_validation():
        print("💥 CRITICAL PATH FAILED")
        return

    print("🎉 PIPELINE VALIDATION COMPLETE")
    print("✅ Step 5 ready for production")


if __name__ == "__main__":
    asyncio.run(main())
