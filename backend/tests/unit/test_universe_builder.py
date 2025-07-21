"""
Unit tests for UniverseBuilder integration with FMPSectorMapper
Tests the sector mapping integration in get_fmp_universe method
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pytest

from services.universe_builder import UniverseBuilder
from services.sector_mapper import FMPSectorMapper

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


class TestUniverseBuilderSectorIntegration:
    """Test suite for UniverseBuilder sector mapping integration"""

    def setup_method(self):
        """Setup test instance"""
        self.universe_builder = UniverseBuilder()

    def test_universe_builder_has_sector_mapper(self):
        """Test that UniverseBuilder instantiates FMPSectorMapper"""
        # Check that sector mapper is available
        assert hasattr(self.universe_builder, "sector_mapper")
        assert isinstance(self.universe_builder.sector_mapper, FMPSectorMapper)

    @patch("mcp.fmp_client.FMPMCPClient.get_stock_screener")
    @pytest.mark.asyncio
    async def test_get_fmp_universe_maps_sectors(self, mock_fmp_client):
        """Test that get_fmp_universe maps FMP sectors to internal sectors"""
        # Mock FMP client response
        mock_fmp_client.return_value = {
            "status": "success",
            "stocks": [
                {
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "exchange": "NASDAQ",
                    "marketCap": 3000000000000,
                    "price": 150.50,
                    "sector": "Technology",  # FMP sector
                    "industry": "Consumer Electronics",
                },
                {
                    "symbol": "JNJ",
                    "companyName": "Johnson & Johnson",
                    "exchange": "NYSE",
                    "marketCap": 400000000000,
                    "price": 160.00,
                    "sector": "Healthcare",  # FMP sector
                    "industry": "Pharmaceuticals",
                },
                {
                    "symbol": "XOM",
                    "companyName": "Exxon Mobil Corp",
                    "exchange": "NYSE",
                    "marketCap": 250000000000,
                    "price": 110.00,
                    "sector": "Energy",  # FMP sector
                    "industry": "Oil & Gas",
                },
            ],
        }

        # Call the method
        result = await self.universe_builder.get_fmp_universe()

        # Verify sectors were mapped correctly
        assert result["status"] == "success"
        stocks = result["stocks"]

        # Find each stock and verify sector mapping
        aapl = next(s for s in stocks if s["symbol"] == "AAPL")
        assert aapl["sector"] == "technology"  # Mapped sector
        assert aapl["original_fmp_sector"] == "Technology"  # Original preserved

        jnj = next(s for s in stocks if s["symbol"] == "JNJ")
        assert jnj["sector"] == "healthcare"
        assert jnj["original_fmp_sector"] == "Healthcare"

        xom = next(s for s in stocks if s["symbol"] == "XOM")
        assert xom["sector"] == "energy"
        assert xom["original_fmp_sector"] == "Energy"

    @patch("mcp.fmp_client.FMPMCPClient.get_stock_screener")
    @pytest.mark.asyncio
    async def test_get_fmp_universe_handles_unknown_sectors(self, mock_fmp_client):
        """Test handling of unknown/unmapped FMP sectors"""
        # Mock FMP client response
        mock_fmp_client.return_value = {
            "status": "success",
            "stocks": [
                {
                    "symbol": "UNKNOWN",
                    "companyName": "Unknown Sector Company",
                    "exchange": "NASDAQ",
                    "marketCap": 100000000,
                    "price": 25.00,
                    "sector": "Unknown Sector",  # Invalid FMP sector
                    "industry": "Unknown Industry",
                },
                {
                    "symbol": "EMPTY",
                    "companyName": "Empty Sector Company",
                    "exchange": "NYSE",
                    "marketCap": 200000000,
                    "price": 15.00,
                    "sector": "",  # Empty sector
                    "industry": "Some Industry",
                },
            ],
        }

        # Call the method
        result = await self.universe_builder.get_fmp_universe()

        # Verify unknown sectors are handled
        stocks = result["stocks"]

        unknown = next(s for s in stocks if s["symbol"] == "UNKNOWN")
        assert unknown["sector"] == "unknown_sector"
        assert unknown["original_fmp_sector"] == "Unknown Sector"

        empty = next(s for s in stocks if s["symbol"] == "EMPTY")
        assert empty["sector"] == "unknown_sector"
        assert empty["original_fmp_sector"] == ""

    @patch("mcp.fmp_client.FMPMCPClient.get_stock_screener")
    @pytest.mark.asyncio
    async def test_get_fmp_universe_preserves_all_original_data(self, mock_fmp_client):
        """Test that all original FMP data is preserved alongside sector mapping"""
        # Mock FMP client response
        mock_fmp_client.return_value = {
            "status": "success",
            "stocks": [
                {
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corp",
                    "exchange": "NASDAQ",
                    "marketCap": 2500000000000,
                    "price": 300.00,
                    "avgVolume": 25000000,
                    "sector": "Technology",
                    "industry": "Software",
                    "beta": 0.9,
                    "pe": 25.5,
                    "eps": 12.0,
                }
            ],
        }

        # Call the method
        result = await self.universe_builder.get_fmp_universe()

        # Verify all original data is preserved
        stocks = result["stocks"]
        msft = stocks[0]

        # Original FMP data should be preserved
        assert msft["symbol"] == "MSFT"
        assert msft["companyName"] == "Microsoft Corp"
        assert msft["exchange"] == "NASDAQ"
        assert msft["marketCap"] == 2500000000000
        assert msft["price"] == 300.00
        assert msft["avgVolume"] == 25000000
        assert msft["industry"] == "Software"
        assert msft["beta"] == 0.9
        assert msft["pe"] == 25.5
        assert msft["eps"] == 12.0

        # Sector mapping should be added
        assert msft["sector"] == "technology"
        assert msft["original_fmp_sector"] == "Technology"

    @patch("mcp.fmp_client.FMPMCPClient.get_stock_screener")
    @pytest.mark.asyncio
    async def test_get_fmp_universe_maps_all_eleven_fmp_sectors(self, mock_fmp_client):
        """Test mapping of all 11 FMP sectors"""
        # Mock FMP client response with all 11 sectors
        mock_fmp_client.return_value = {
            "status": "success",
            "stocks": [
                {
                    "symbol": "MAT",
                    "sector": "Basic Materials",
                    "companyName": "Materials Co",
                    "exchange": "NYSE",
                    "marketCap": 1000000000,
                    "price": 50,
                },
                {
                    "symbol": "COM",
                    "sector": "Communication Services",
                    "companyName": "Comms Co",
                    "exchange": "NASDAQ",
                    "marketCap": 1000000000,
                    "price": 50,
                },
                {
                    "symbol": "CYC",
                    "sector": "Consumer Cyclical",
                    "companyName": "Cyclical Co",
                    "exchange": "NYSE",
                    "marketCap": 1000000000,
                    "price": 50,
                },
                {
                    "symbol": "DEF",
                    "sector": "Consumer Defensive",
                    "companyName": "Defensive Co",
                    "exchange": "NASDAQ",
                    "marketCap": 1000000000,
                    "price": 50,
                },
                {
                    "symbol": "ENE",
                    "sector": "Energy",
                    "companyName": "Energy Co",
                    "exchange": "NYSE",
                    "marketCap": 1000000000,
                    "price": 50,
                },
                {
                    "symbol": "FIN",
                    "sector": "Financial Services",
                    "companyName": "Financial Co",
                    "exchange": "NASDAQ",
                    "marketCap": 1000000000,
                    "price": 50,
                },
                {
                    "symbol": "HEA",
                    "sector": "Healthcare",
                    "companyName": "Healthcare Co",
                    "exchange": "NYSE",
                    "marketCap": 1000000000,
                    "price": 50,
                },
                {
                    "symbol": "IND",
                    "sector": "Industrials",
                    "companyName": "Industrial Co",
                    "exchange": "NASDAQ",
                    "marketCap": 1000000000,
                    "price": 50,
                },
                {
                    "symbol": "REA",
                    "sector": "Real Estate",
                    "companyName": "Real Estate Co",
                    "exchange": "NYSE",
                    "marketCap": 1000000000,
                    "price": 50,
                },
                {
                    "symbol": "TEC",
                    "sector": "Technology",
                    "companyName": "Tech Co",
                    "exchange": "NASDAQ",
                    "marketCap": 1000000000,
                    "price": 50,
                },
                {
                    "symbol": "UTI",
                    "sector": "Utilities",
                    "companyName": "Utility Co",
                    "exchange": "NYSE",
                    "marketCap": 1000000000,
                    "price": 50,
                },
            ],
        }

        # Call the method
        result = await self.universe_builder.get_fmp_universe()

        # Verify all sectors are mapped correctly
        stocks = result["stocks"]
        sector_mappings = {}

        for stock in stocks:
            sector_mappings[stock["original_fmp_sector"]] = stock["sector"]

        expected_mappings = {
            "Basic Materials": "basic_materials",
            "Communication Services": "communication_services",
            "Consumer Cyclical": "consumer_cyclical",
            "Consumer Defensive": "consumer_defensive",
            "Energy": "energy",
            "Financial Services": "financial_services",
            "Healthcare": "healthcare",
            "Industrials": "industrials",
            "Real Estate": "real_estate",
            "Technology": "technology",
            "Utilities": "utilities",
        }

        assert sector_mappings == expected_mappings

    @patch("mcp.fmp_client.FMPMCPClient.get_stock_screener")
    @pytest.mark.asyncio
    async def test_get_fmp_universe_error_handling(self, mock_fmp_client):
        """Test error handling when FMP data retrieval fails"""
        # Mock FMP error
        mock_fmp_client.side_effect = Exception("FMP API Error")

        # Call the method
        result = await self.universe_builder.get_fmp_universe()

        # Verify error is handled gracefully
        assert result["status"] == "error"
        assert "FMP API Error" in result["message"]
        assert result["stocks"] == []
        assert result["universe_size"] == 0
