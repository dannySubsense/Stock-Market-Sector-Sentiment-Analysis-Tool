"""
Integration Tests for 1D Volume Weighting Engine - Step 3 Implementation
Tests volume weighting with real market data and database integration
"""

import pytest
import asyncio
from typing import List
from unittest.mock import patch

from services.volume_weighting_1d import (
    VolumeWeightingEngine1D,
    StockVolumeData,
    WeightedSectorResult,
)
from services.stock_data_retrieval_1d import StockDataRetrieval1D
from core.database import SessionLocal
from models.stock_universe import StockUniverse


class TestVolumeWeightingIntegration:
    """Integration tests for volume weighting with real data"""

    @pytest.fixture
    def engine(self):
        """Create volume weighting engine instance"""
        return VolumeWeightingEngine1D()

    @pytest.fixture
    def data_retrieval(self):
        """Create stock data retrieval service"""
        return StockDataRetrieval1D()

    @pytest.fixture
    def sample_tech_stocks(self):
        """Get sample technology sector stocks from database"""
        with SessionLocal() as db:
            stocks = (
                db.query(StockUniverse)
                .filter(StockUniverse.sector == "Technology")
                .limit(5)
                .all()
            )
            return [stock.symbol for stock in stocks]

    @pytest.mark.asyncio
    async def test_volume_weighting_with_real_market_data(
        self, engine, data_retrieval, sample_tech_stocks
    ):
        """Test volume weighting calculation with real market data"""
        if not sample_tech_stocks:
            pytest.skip("No technology stocks found in database")

        # Retrieve real market data for first 3 stocks
        market_data = {}
        for symbol in sample_tech_stocks[:3]:
            stock_data = await data_retrieval.get_1d_stock_data(symbol)
            if stock_data:
                market_data[symbol] = {
                    "status": "success",
                    "quote": {
                        "volume": stock_data.current_volume,
                        "avgVolume": stock_data.avg_20_day_volume,
                        "changesPercentage": (
                            (stock_data.current_price - stock_data.previous_close)
                            / stock_data.previous_close
                            * 100
                        ),
                        "marketCap": 1000000000,  # Mock market cap
                    },
                }

        # Convert to volume data format
        volume_data = []
        for symbol, data in market_data.items():
            if data["status"] == "success" and data["quote"]:
                quote = data["quote"]
                volume_data.append(
                    StockVolumeData(
                        symbol=symbol,
                        current_volume=int(quote.get("volume", 0)),
                        avg_volume_20d=int(
                            quote.get("avgVolume", quote.get("volume", 0))
                        ),
                        price_change_1d=float(quote.get("changesPercentage", 0.0)),
                        market_cap=quote.get("marketCap"),
                    )
                )

        # Calculate weighted sector performance
        result = engine.calculate_weighted_sector_performance("technology", volume_data)

        # Verify results
        assert isinstance(result, WeightedSectorResult)
        assert result.sector == "technology"
        assert result.stock_count >= 0
        assert result.volatility_multiplier > 0
        assert 0.0 <= result.confidence_score <= 1.0

        # Log results for analysis
        print(f"\nVolume Weighting Integration Test Results:")
        print(f"Sector: {result.sector}")
        print(f"Stocks processed: {result.stock_count}")
        print(f"Weighted performance: {result.weighted_performance:.2f}%")
        print(f"Total weight: {result.total_weight:.2f}")
        print(f"Outlier count: {result.outlier_count}")
        print(f"Confidence: {result.confidence_score:.2f}")

    @pytest.mark.asyncio
    async def test_volume_weighting_multiple_sectors(self, engine, data_retrieval):
        """Test volume weighting across multiple sectors"""
        sectors_to_test = ["Technology", "Healthcare", "Financial"]

        with SessionLocal() as db:
            sector_results = {}

            for sector in sectors_to_test:
                # Get 3 stocks from each sector
                stocks = (
                    db.query(StockUniverse)
                    .filter(StockUniverse.sector == sector)
                    .limit(3)
                    .all()
                )

                if not stocks:
                    continue

                symbols = [stock.symbol for stock in stocks]

                # Get market data
                market_data = {}
                for symbol in symbols:
                    stock_data = await data_retrieval.get_1d_stock_data(symbol)
                    if stock_data:
                        market_data[symbol] = {
                            "status": "success",
                            "quote": {
                                "volume": stock_data.current_volume,
                                "avgVolume": stock_data.avg_20_day_volume,
                                "changesPercentage": (
                                    (
                                        stock_data.current_price
                                        - stock_data.previous_close
                                    )
                                    / stock_data.previous_close
                                    * 100
                                ),
                            },
                        }

                # Convert to volume data
                volume_data = []
                for symbol, data in market_data.items():
                    if data["status"] == "success" and data["quote"]:
                        quote = data["quote"]
                        volume_data.append(
                            StockVolumeData(
                                symbol=symbol,
                                current_volume=int(quote.get("volume", 0)),
                                avg_volume_20d=int(
                                    quote.get("avgVolume", quote.get("volume", 0))
                                ),
                                price_change_1d=float(
                                    quote.get("changesPercentage", 0.0)
                                ),
                            )
                        )

                # Calculate weighted performance
                result = engine.calculate_weighted_sector_performance(
                    sector.lower(), volume_data
                )
                sector_results[sector] = result

        # Verify all calculations completed
        assert len(sector_results) > 0

        for sector, result in sector_results.items():
            assert result.sector == sector.lower()
            assert result.volatility_multiplier > 0
            assert 0.0 <= result.confidence_score <= 1.0

            print(f"\n{sector} Sector Results:")
            print(f"  Performance: {result.weighted_performance:.2f}%")
            print(f"  Stocks: {result.stock_count}")
            print(f"  Confidence: {result.confidence_score:.2f}")

    def test_volume_weighting_with_database_stocks(self, engine):
        """Test volume weighting with stocks directly from database"""
        with SessionLocal() as db:
            # Get some stocks from database
            stocks = (
                db.query(StockUniverse)
                .filter(StockUniverse.avg_daily_volume > 1000)  # Ensure minimum volume
                .limit(10)
                .all()
            )

            if not stocks:
                pytest.skip("No stocks with sufficient volume found in database")

            # Create mock volume data based on database stocks
            volume_data = []
            for stock in stocks:
                # Use database volume as current, simulate average
                current_vol = int(stock.avg_daily_volume or 10000)
                avg_volume = int(current_vol * 0.8)

                volume_data.append(
                    StockVolumeData(
                        symbol=stock.symbol,
                        current_volume=current_vol,
                        avg_volume_20d=avg_volume,
                        price_change_1d=1.5,  # Mock price change since it's not in database
                        market_cap=float(stock.market_cap or 0.0),
                    )
                )

            # Calculate weighted performance
            result = engine.calculate_weighted_sector_performance("mixed", volume_data)

            # Verify calculation works with database data
            assert isinstance(result, WeightedSectorResult)
            assert result.total_weight >= 0
            assert 0.0 <= result.confidence_score <= 1.0

    def test_volume_data_validation_with_real_data(self, engine):
        """Test volume data validation with realistic scenarios"""
        # Create realistic test data with various edge cases
        test_data = [
            StockVolumeData("VALID1", 100000, 90000, 2.5),
            StockVolumeData("VALID2", 250000, 200000, -1.8),
            StockVolumeData("LOW_VOL", 500, 800, 1.0),  # Below threshold
            StockVolumeData("NO_AVG", 100000, None, 3.2),  # No average volume
            StockVolumeData("OUTLIER", 1000000, 100000, 5.0),  # Volume outlier
            StockVolumeData("EXTREME", 50000, 40000, 75.0),  # Extreme price change
        ]

        valid_stocks, errors = engine.validate_volume_data(test_data)

        # Should validate all but flag issues
        assert len(valid_stocks) >= 4  # All except maybe empty symbol cases
        assert len(errors) >= 1  # Should catch extreme price change

        # Check that extreme price change is flagged
        extreme_errors = [err for err in errors if "Extreme price change" in err]
        assert len(extreme_errors) == 1

    @pytest.mark.asyncio
    async def test_volume_weighting_performance_benchmark(self, engine, data_retrieval):
        """Test performance of volume weighting calculation"""
        import time

        with SessionLocal() as db:
            # Get a larger set of stocks for performance testing
            stocks = db.query(StockUniverse).limit(20).all()

            if len(stocks) < 10:
                pytest.skip("Insufficient stocks for performance test")

            symbols = [stock.symbol for stock in stocks]

            # Time the data retrieval
            start_time = time.time()
            market_data = {}
            for symbol in symbols[:10]:
                stock_data = await data_retrieval.get_1d_stock_data(symbol)
                if stock_data:
                    market_data[symbol] = {
                        "status": "success",
                        "quote": {
                            "volume": stock_data.current_volume,
                            "avgVolume": stock_data.avg_20_day_volume,
                            "changesPercentage": (
                                (stock_data.current_price - stock_data.previous_close)
                                / stock_data.previous_close
                                * 100
                            ),
                        },
                    }
            data_retrieval_time = time.time() - start_time

            # Convert to volume data
            volume_data = []
            for symbol, data in market_data.items():
                if data["status"] == "success" and data["quote"]:
                    quote = data["quote"]
                    volume_data.append(
                        StockVolumeData(
                            symbol=symbol,
                            current_volume=int(quote.get("volume", 10000)),
                            avg_volume_20d=int(
                                quote.get("avgVolume", quote.get("volume", 10000))
                            ),
                            price_change_1d=float(quote.get("changesPercentage", 0.0)),
                        )
                    )

            # Time the volume weighting calculation
            start_time = time.time()
            result = engine.calculate_weighted_sector_performance("test", volume_data)
            calculation_time = time.time() - start_time

            # Performance assertions
            assert data_retrieval_time < 5.0  # Should be fast for 10 stocks
            assert calculation_time < 0.1  # Volume weighting should be very fast
            assert result.stock_count >= 0

            print(f"\nPerformance Benchmark Results:")
            print(
                f"Data retrieval time: {data_retrieval_time:.3f}s for {len(symbols[:10])} stocks"
            )
            print(
                f"Volume weighting time: {calculation_time:.3f}s for {result.stock_count} valid stocks"
            )
            print(
                f"Total processing time: {data_retrieval_time + calculation_time:.3f}s"
            )


class TestVolumeWeightingEdgeCases:
    """Test edge cases and error handling in integration scenarios"""

    @pytest.fixture
    def engine(self):
        return VolumeWeightingEngine1D()

    def test_empty_sector_handling(self, engine):
        """Test volume weighting with empty sector data"""
        result = engine.calculate_weighted_sector_performance("empty", [])

        assert result.sector == "empty"
        assert result.stock_count == 0
        assert result.weighted_performance == 0.0
        assert result.confidence_score == 0.0

    def test_all_invalid_stocks(self, engine):
        """Test volume weighting when all stocks are invalid"""
        invalid_stocks = [
            StockVolumeData("LOW1", 100, 200, 1.0),  # Below volume threshold
            StockVolumeData("LOW2", 500, 800, 2.0),  # Below volume threshold
        ]

        result = engine.calculate_weighted_sector_performance("invalid", invalid_stocks)

        assert result.stock_count == 0
        assert result.confidence_score == 0.0

    def test_mixed_data_quality(self, engine):
        """Test volume weighting with mixed data quality"""
        mixed_stocks = [
            StockVolumeData("GOOD1", 100000, 90000, 2.5),
            StockVolumeData("GOOD2", 150000, 120000, -1.8),
            StockVolumeData("NO_AVG", 80000, None, 1.5),  # No average volume
            StockVolumeData(
                "OUTLIER", 600000, 100000, 3.0
            ),  # Volume outlier (6x > 5x threshold)
            StockVolumeData("LOW_VOL", 800, 1000, 1.0),  # Below threshold
        ]

        result = engine.calculate_weighted_sector_performance("mixed", mixed_stocks)

        # Should process valid stocks and handle edge cases
        assert result.stock_count >= 2  # At least the good stocks
        assert result.outlier_count >= 1  # Should detect outlier
        assert result.confidence_score > 0.0  # Should have some confidence
