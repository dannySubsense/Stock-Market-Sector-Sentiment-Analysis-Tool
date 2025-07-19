"""
Unit tests for StockUniverse model with sector fields
Tests the updated model with sector and original_fmp_sector fields
"""

import sys
from pathlib import Path

from models.stock_universe import StockUniverse

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


class TestStockUniverseModel:
    """Test suite for StockUniverse model with sector fields"""

    def test_create_stock_universe_with_sector_fields(self):
        """Test creating StockUniverse with new sector fields"""
        stock = StockUniverse(
            symbol="AAPL",
            company_name="Apple Inc.",
            exchange="NASDAQ",
            market_cap=3000000000000,
            current_price=150.50,
            avg_daily_volume=80000000,
            sector="technology",
            original_fmp_sector="Technology",
            is_active=True,
        )

        assert stock.symbol == "AAPL"
        assert stock.sector == "technology"
        assert stock.original_fmp_sector == "Technology"
        assert stock.is_active is True

    def test_stock_universe_sector_field_types(self):
        """Test sector field types and validation"""
        stock = StockUniverse(
            symbol="MSFT",
            company_name="Microsoft Corp",
            exchange="NASDAQ",
            market_cap=2500000000000,
            current_price=300.00,
            avg_daily_volume=25000000,
            sector="technology",
            original_fmp_sector="Technology",
            is_active=True,
        )

        # Test field types
        assert isinstance(stock.sector, str)
        assert isinstance(stock.original_fmp_sector, str)
        assert isinstance(stock.is_active, bool)

    def test_stock_universe_with_all_fmp_sectors(self):
        """Test StockUniverse with all possible FMP sector mappings"""
        fmp_sector_mappings = [
            ("Basic Materials", "basic_materials"),
            ("Communication Services", "communication_services"),
            ("Consumer Cyclical", "consumer_cyclical"),
            ("Consumer Defensive", "consumer_defensive"),
            ("Energy", "energy"),
            ("Financial Services", "financial_services"),
            ("Healthcare", "healthcare"),
            ("Industrials", "industrials"),
            ("Real Estate", "real_estate"),
            ("Technology", "technology"),
            ("Utilities", "utilities"),
        ]

        for original_fmp, mapped_sector in fmp_sector_mappings:
            stock = StockUniverse(
                symbol=f"TEST{mapped_sector.upper()[:3]}",
                company_name=f"Test {mapped_sector.title()} Company",
                exchange="NASDAQ",
                market_cap=1000000000,
                current_price=50.00,
                avg_daily_volume=1000000,
                sector=mapped_sector,
                original_fmp_sector=original_fmp,
                is_active=True,
            )

            assert stock.sector == mapped_sector
            assert stock.original_fmp_sector == original_fmp

    def test_stock_universe_sector_preservation(self):
        """Test that original FMP sector data is preserved"""
        stock = StockUniverse(
            symbol="JNJ",
            company_name="Johnson & Johnson",
            exchange="NYSE",
            market_cap=400000000000,
            current_price=160.00,
            avg_daily_volume=15000000,
            sector="healthcare",  # Our internal mapping
            original_fmp_sector="Healthcare",  # Original FMP data
            is_active=True,
        )

        # Both fields should be preserved
        assert stock.sector == "healthcare"
        assert stock.original_fmp_sector == "Healthcare"

        # They should be different (internal vs original)
        assert stock.sector != stock.original_fmp_sector

    def test_stock_universe_optional_fields(self):
        """Test that sector fields can be None/empty"""
        stock = StockUniverse(
            symbol="UNKNOWN",
            company_name="Unknown Company",
            exchange="NASDAQ",
            market_cap=100000000,
            current_price=10.00,
            avg_daily_volume=500000,
            sector=None,  # Could be None for unknown sectors
            original_fmp_sector="",  # Could be empty string
            is_active=True,
        )

        assert stock.sector is None
        assert stock.original_fmp_sector == ""

    def test_stock_universe_theme_slot_sector(self):
        """Test StockUniverse with theme slot sector"""
        stock = StockUniverse(
            symbol="BTCS",
            company_name="Bitcoin Treasury Stock",
            exchange="NASDAQ",
            market_cap=50000000,
            current_price=25.00,
            avg_daily_volume=2000000,
            sector="theme_slot",  # Special theme slot
            original_fmp_sector="Technology",  # Original FMP classification
            is_active=True,
        )

        assert stock.sector == "theme_slot"
        assert stock.original_fmp_sector == "Technology"

    def test_stock_universe_market_cap_filters(self):
        """Test that model works with various market cap ranges"""
        # Micro cap example
        micro_cap = StockUniverse(
            symbol="MICRO",
            company_name="Micro Cap Co",
            exchange="NASDAQ",
            market_cap=50000000,  # $50M
            current_price=5.00,
            avg_daily_volume=1200000,
            sector="basic_materials",
            original_fmp_sector="Basic Materials",
            is_active=True,
        )

        # Small cap example
        small_cap = StockUniverse(
            symbol="SMALL",
            company_name="Small Cap Corp",
            exchange="NYSE",
            market_cap=1500000000,  # $1.5B
            current_price=75.00,
            avg_daily_volume=3000000,
            sector="industrials",
            original_fmp_sector="Industrials",
            is_active=True,
        )

        assert micro_cap.market_cap < 300000000  # Under $300M
        assert small_cap.market_cap > 300000000  # Over $300M
        assert small_cap.market_cap < 2000000000  # Under $2B
